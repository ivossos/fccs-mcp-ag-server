"""
Custom metadata validation script for FCCS.
Since the /validatemetadata endpoint is not available in the API,
this script validates metadata by checking all dimensions and their members.

Guardrails applied:
- Rate limiting to prevent API overload
- Timeout handling for API calls
- Resource limits (max dimensions/members)
- Input validation
- Safe file writing
- Error recovery and retry logic
- Progress tracking
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.dimensions import get_dimensions, get_members

# Guardrail constants
MAX_DIMENSIONS = 100  # Maximum number of dimensions to process
MAX_MEMBERS_PER_DIMENSION = 10000  # Maximum members per dimension to validate
MAX_TOTAL_MEMBERS = 100000  # Maximum total members across all dimensions
API_CALL_DELAY = 0.5  # Delay between API calls (seconds)
API_TIMEOUT = 30.0  # Timeout for API calls (seconds)
MAX_RETRIES = 3  # Maximum retry attempts for failed API calls
MAX_LOG_FILE_SIZE_MB = 100  # Maximum log file size in MB


class ValidationIssue:
    """Represents a validation issue found during metadata check."""
    
    def __init__(self, severity: str, dimension: str, issue_type: str, message: str, details: str = ""):
        if severity not in ["ERROR", "WARNING", "INFO"]:
            severity = "WARNING"  # Default to WARNING for invalid severity
        self.severity = severity
        self.dimension = str(dimension)[:200] if dimension else "UNKNOWN"  # Limit dimension name length
        self.issue_type = str(issue_type)[:100] if issue_type else "UNKNOWN"  # Limit issue type length
        self.message = str(message)[:1000] if message else ""  # Limit message length
        self.details = str(details)[:2000] if details else ""  # Limit details length
        self.timestamp = datetime.now().isoformat()
    
    def __str__(self):
        return f"[{self.severity}] {self.dimension}: {self.message}"


async def safe_api_call_with_retry(call_func, *args, max_retries: int = MAX_RETRIES, **kwargs):
    """Safely call an API function with retry logic and timeout."""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = await asyncio.wait_for(
                call_func(*args, **kwargs),
                timeout=API_TIMEOUT
            )
            return result
        except asyncio.TimeoutError:
            last_error = f"Timeout after {API_TIMEOUT}s"
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    
    raise Exception(f"API call failed after {max_retries} attempts: {last_error}")


async def validate_metadata(log_file_name: str = "metadata_validation_log.txt") -> List[ValidationIssue]:
    """Validate application metadata by checking all dimensions and members."""
    
    issues: List[ValidationIssue] = []
    total_members_processed = 0
    
    try:
        # Input validation for log file name
        if not log_file_name or not isinstance(log_file_name, str):
            log_file_name = "metadata_validation_log.txt"
        if len(log_file_name) > 255:
            log_file_name = log_file_name[:255]
        
        # Initialize agent
        config = load_config()
        await initialize_agent(config)
        
        # Get all dimensions with retry and timeout
        print("Retrieving dimensions...")
        try:
            dims_result = await safe_api_call_with_retry(get_dimensions)
        except Exception as e:
            issues.append(ValidationIssue(
                severity="ERROR",
                dimension="SYSTEM",
                issue_type="API_ERROR",
                message="Failed to retrieve dimensions after retries",
                details=str(e)
            ))
            return issues
        
        if dims_result.get("status") != "success":
            issues.append(ValidationIssue(
                severity="ERROR",
                dimension="SYSTEM",
                issue_type="API_ERROR",
                message="Failed to retrieve dimensions",
                details=str(dims_result.get("error", "Unknown error"))
            ))
            return issues
        
        dimensions = dims_result.get("data", {}).get("items", [])
        
        if not dimensions:
            issues.append(ValidationIssue(
                severity="WARNING",
                dimension="SYSTEM",
                issue_type="NO_DIMENSIONS",
                message="No dimensions found in application",
                details="Application may be empty or inaccessible"
            ))
            return issues
        
        # Resource limit: Check maximum dimensions
        if len(dimensions) > MAX_DIMENSIONS:
            issues.append(ValidationIssue(
                severity="WARNING",
                dimension="SYSTEM",
                issue_type="RESOURCE_LIMIT",
                message=f"Too many dimensions ({len(dimensions)}), processing first {MAX_DIMENSIONS}",
                details=f"Limit: {MAX_DIMENSIONS}"
            ))
            dimensions = dimensions[:MAX_DIMENSIONS]
        
        print(f"Found {len(dimensions)} dimensions. Validating...")
        
        # Validate each dimension with rate limiting
        for idx, dim in enumerate(dimensions, 1):
            dim_name = dim.get("name", "UNKNOWN")
            print(f"  [{idx}/{len(dimensions)}] Validating dimension: {dim_name}")
            
            # Check if dimension has required properties
            if not dim.get("name"):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    dimension=dim_name,
                    issue_type="MISSING_NAME",
                    message="Dimension missing name property"
                ))
                continue
            
            # Rate limiting: Add delay between API calls
            if idx > 1:
                await asyncio.sleep(API_CALL_DELAY)
            
            # Check resource limits before processing
            if total_members_processed >= MAX_TOTAL_MEMBERS:
                issues.append(ValidationIssue(
                    severity="WARNING",
                    dimension=dim_name,
                    issue_type="RESOURCE_LIMIT",
                    message=f"Reached maximum total members limit ({MAX_TOTAL_MEMBERS})",
                    details="Skipping remaining dimensions"
                ))
                break
            
            # Try to get members for this dimension with retry
            try:
                members_result = await safe_api_call_with_retry(get_members, dim_name)
                
                if members_result.get("status") != "success":
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        dimension=dim_name,
                        issue_type="MEMBERS_RETRIEVAL_FAILED",
                        message="Failed to retrieve members",
                        details=str(members_result.get("error", "Unknown error"))
                    ))
                    continue
                
                members_data = members_result.get("data", {})
                members = members_data.get("items", [])
                
                if not members:
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        dimension=dim_name,
                        issue_type="NO_MEMBERS",
                        message="Dimension has no members",
                        details="This may be expected for some dimension types"
                    ))
                    continue
                
                # Resource limit: Check maximum members per dimension
                original_count = len(members)
                if original_count > MAX_MEMBERS_PER_DIMENSION:
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        dimension=dim_name,
                        issue_type="RESOURCE_LIMIT",
                        message=f"Too many members ({original_count}), validating first {MAX_MEMBERS_PER_DIMENSION}",
                        details=f"Limit: {MAX_MEMBERS_PER_DIMENSION}"
                    ))
                    members = members[:MAX_MEMBERS_PER_DIMENSION]
                
                # Check if we've exceeded total member limit
                if total_members_processed + len(members) > MAX_TOTAL_MEMBERS:
                    remaining = MAX_TOTAL_MEMBERS - total_members_processed
                    if remaining > 0:
                        members = members[:remaining]
                    else:
                        break
                
                # Validate members
                member_count = len(members)
                total_members_processed += member_count
                print(f"    Found {member_count} members (Total processed: {total_members_processed})")
                
                # Check for members without names
                nameless_members = [m for m in members if not m.get("name")]
                if nameless_members:
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        dimension=dim_name,
                        issue_type="MEMBER_MISSING_NAME",
                        message=f"Found {len(nameless_members)} members without names",
                        details=f"Total members: {member_count}"
                    ))
                
                # Check for duplicate member names
                member_names = [m.get("name") for m in members if m.get("name")]
                duplicates = [name for name in member_names if member_names.count(name) > 1]
                if duplicates:
                    unique_duplicates = list(set(duplicates))
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        dimension=dim_name,
                        issue_type="DUPLICATE_MEMBER_NAMES",
                        message=f"Found {len(unique_duplicates)} duplicate member names",
                        details=f"Duplicates: {', '.join(unique_duplicates[:10])}"
                    ))
                
            except Exception as e:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    dimension=dim_name,
                    issue_type="EXCEPTION",
                    message=f"Exception while validating dimension: {str(e)}",
                    details=type(e).__name__
                ))
        
        print(f"\nValidation complete. Found {len(issues)} issues. Processed {total_members_processed} total members.")
        
    except Exception as e:
        issues.append(ValidationIssue(
            severity="ERROR",
            dimension="SYSTEM",
            issue_type="SYSTEM_ERROR",
            message=f"System error during validation: {str(e)}",
            details=type(e).__name__
        ))
    
    finally:
        try:
            await close_agent()
        except Exception:
            pass  # Ignore errors during cleanup
    
    return issues


def generate_log_file(issues: List[ValidationIssue], log_file_name: str):
    """Generate a log file with validation results."""
    
    # Input validation
    if not log_file_name or not isinstance(log_file_name, str):
        log_file_name = "metadata_validation_log.txt"
    
    log_path = Path(log_file_name)
    
    # Check if file would be too large (estimate)
    estimated_size_mb = (len(issues) * 500) / (1024 * 1024)  # Rough estimate: 500 bytes per issue
    if estimated_size_mb > MAX_LOG_FILE_SIZE_MB:
        issues.append(ValidationIssue(
            severity="WARNING",
            dimension="SYSTEM",
            issue_type="FILE_SIZE_LIMIT",
            message=f"Log file would exceed size limit ({MAX_LOG_FILE_SIZE_MB}MB)",
            details=f"Estimated size: {estimated_size_mb:.2f}MB, Issues: {len(issues)}"
        ))
        # Limit issues to prevent huge file
        max_issues = int((MAX_LOG_FILE_SIZE_MB * 1024 * 1024) / 500)
        if len(issues) > max_issues:
            issues = issues[:max_issues]
    
    # Safe file writing with error handling
    try:
        with open(log_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("FCCS METADATA VALIDATION LOG\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Total Issues Found: {len(issues)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Group issues by severity
        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]
        infos = [i for i in issues if i.severity == "INFO"]
        
        f.write(f"SUMMARY\n")
        f.write(f"  Errors:   {len(errors)}\n")
        f.write(f"  Warnings: {len(warnings)}\n")
        f.write(f"  Info:     {len(infos)}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        
        # Write errors
        if errors:
            f.write("ERRORS\n")
            f.write("-" * 80 + "\n")
            for issue in errors:
                f.write(f"\n[{issue.severity}] {issue.timestamp}\n")
                f.write(f"Dimension: {issue.dimension}\n")
                f.write(f"Type: {issue.issue_type}\n")
                f.write(f"Message: {issue.message}\n")
                if issue.details:
                    f.write(f"Details: {issue.details}\n")
                f.write("\n")
        
        # Write warnings
        if warnings:
            f.write("\n" + "=" * 80 + "\n")
            f.write("WARNINGS\n")
            f.write("-" * 80 + "\n")
            for issue in warnings:
                f.write(f"\n[{issue.severity}] {issue.timestamp}\n")
                f.write(f"Dimension: {issue.dimension}\n")
                f.write(f"Type: {issue.issue_type}\n")
                f.write(f"Message: {issue.message}\n")
                if issue.details:
                    f.write(f"Details: {issue.details}\n")
                f.write("\n")
        
        # Write info
        if infos:
            f.write("\n" + "=" * 80 + "\n")
            f.write("INFORMATIONAL\n")
            f.write("-" * 80 + "\n")
            for issue in infos:
                f.write(f"\n[{issue.severity}] {issue.timestamp}\n")
                f.write(f"Dimension: {issue.dimension}\n")
                f.write(f"Type: {issue.issue_type}\n")
                f.write(f"Message: {issue.message}\n")
                if issue.details:
                    f.write(f"Details: {issue.details}\n")
                f.write("\n")
        
        # Write all issues in detail
        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED ISSUE LIST\n")
        f.write("=" * 80 + "\n\n")
        
        for idx, issue in enumerate(issues, 1):
            f.write(f"Issue #{idx}\n")
            f.write(f"  Severity: {issue.severity}\n")
            f.write(f"  Dimension: {issue.dimension}\n")
            f.write(f"  Type: {issue.issue_type}\n")
            f.write(f"  Message: {issue.message}\n")
            if issue.details:
                f.write(f"  Details: {issue.details}\n")
            f.write(f"  Timestamp: {issue.timestamp}\n")
            f.write("\n")
        
        # Check actual file size
        file_size_mb = log_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_LOG_FILE_SIZE_MB:
            print(f"Warning: Log file size ({file_size_mb:.2f}MB) exceeds limit ({MAX_LOG_FILE_SIZE_MB}MB)")
    
    except IOError as e:
        print(f"Error writing log file: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error writing log file: {e}")
        raise
    
    print(f"\nLog file generated: {log_path.absolute()}")
    return log_path


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate FCCS application metadata")
    parser.add_argument(
        "--log-file",
        default="metadata_validation_log.txt",
        help="Name of the log file to generate (default: metadata_validation_log.txt)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("FCCS METADATA VALIDATION")
    print("=" * 80)
    print()
    
    issues = await validate_metadata(args.log_file)
    log_path = generate_log_file(issues, args.log_file)
    
    # Print summary
    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Issues: {len(issues)}")
    print(f"  Errors:   {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Info:     {len(issues) - len(errors) - len(warnings)}")
    print(f"\nLog file: {log_path.absolute()}")
    
    if errors:
        print("\n⚠️  Validation completed with ERRORS. Please review the log file.")
        return 1
    elif warnings:
        print("\n⚠️  Validation completed with WARNINGS. Please review the log file.")
        return 0
    else:
        print("\n✅ Validation completed successfully. No issues found.")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

