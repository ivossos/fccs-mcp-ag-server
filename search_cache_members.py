"""Search cache files for specific member names or patterns."""

import csv
import sys
from pathlib import Path
from typing import List, Dict, Optional


def search_entity_cache(search_terms: List[str], cache_file: str = "Ravi_ExportedMetadata_Entity.csv") -> Dict[str, List[Dict]]:
    """Search entity cache file for member names."""
    results = {}
    
    if not Path(cache_file).exists():
        print(f"[ERROR] Cache file not found: {cache_file}")
        return results
    
    with open(cache_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            # Handle BOM in column name
            entity_name = row.get('Entity', row.get('\ufeffEntity', '')).strip()
            if not entity_name:
                continue
            
            # Check each search term
            for term in search_terms:
                term_upper = term.upper()
                entity_upper = entity_name.upper()
                
                # Exact match
                if entity_name == term or entity_upper == term_upper:
                    if term not in results:
                        results[term] = []
                    results[term].append({
                        'name': entity_name,
                        'parent': row.get('Parent', ''),
                        'alias': row.get('Alias: Default', ''),
                        'type': 'exact'
                    })
                # Partial match (contains)
                elif term_upper in entity_upper or entity_upper in term_upper:
                    if term not in results:
                        results[term] = []
                    results[term].append({
                        'name': entity_name,
                        'parent': row.get('Parent', ''),
                        'alias': row.get('Alias: Default', ''),
                        'type': 'partial'
                    })
                # Pattern match (starts with letter + number)
                elif term[0].isalpha() and term[1:].isdigit():
                    if entity_name[0].isalpha() and entity_name[1:].isdigit():
                        if term[0].upper() == entity_name[0].upper():
                            if term not in results:
                                results[term] = []
                            results[term].append({
                                'name': entity_name,
                                'parent': row.get('Parent', ''),
                                'alias': row.get('Alias: Default', ''),
                                'type': 'pattern'
                            })
    
    return results


def search_account_cache(search_terms: List[str], cache_file: str = "Ravi_ExportedMetadata_Account.csv") -> Dict[str, List[Dict]]:
    """Search account cache file for member names."""
    results = {}
    
    if not Path(cache_file).exists():
        print(f"[ERROR] Cache file not found: {cache_file}")
        return results
    
    with open(cache_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            # Handle BOM in column name
            account_name = row.get('Account', row.get('\ufeffAccount', '')).strip()
            if not account_name:
                continue
            
            # Check each search term
            for term in search_terms:
                term_upper = term.upper()
                account_upper = account_name.upper()
                
                # Exact match
                if account_name == term or account_upper == term_upper:
                    if term not in results:
                        results[term] = []
                    results[term].append({
                        'name': account_name,
                        'parent': row.get('Parent', ''),
                        'alias': row.get('Alias: Default', ''),
                        'type': 'exact'
                    })
                # Partial match (contains)
                elif term_upper in account_upper or account_upper in term_upper:
                    if term not in results:
                        results[term] = []
                    results[term].append({
                        'name': account_name,
                        'parent': row.get('Parent', ''),
                        'alias': row.get('Alias: Default', ''),
                        'type': 'partial'
                    })
                # Pattern match (starts with letter + number)
                elif term[0].isalpha() and term[1:].isdigit():
                    if account_name[0].isalpha() and account_name[1:].isdigit():
                        if term[0].upper() == account_name[0].upper():
                            if term not in results:
                                results[term] = []
                            results[term].append({
                                'name': account_name,
                                'parent': row.get('Parent', ''),
                                'alias': row.get('Alias: Default', ''),
                                'type': 'pattern'
                            })
    
    return results


def list_all_entities(cache_file: str = "Ravi_ExportedMetadata_Entity.csv", limit: int = 50) -> List[str]:
    """List all entity names from cache."""
    entities = []
    
    if not Path(cache_file).exists():
        return entities
    
    with open(cache_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            # Handle BOM in column name
            entity_name = row.get('Entity', row.get('\ufeffEntity', '')).strip()
            if entity_name:
                entities.append(entity_name)
                if len(entities) >= limit:
                    break
    
    return entities


def list_all_accounts(cache_file: str = "Ravi_ExportedMetadata_Account.csv", limit: int = 50) -> List[str]:
    """List all account names from cache."""
    accounts = []
    
    if not Path(cache_file).exists():
        return accounts
    
    with open(cache_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            # Handle BOM in column name
            account_name = row.get('Account', row.get('\ufeffAccount', '')).strip()
            if account_name:
                accounts.append(account_name)
                if len(accounts) >= limit:
                    break
    
    return accounts


def main():
    """Main search function."""
    print("=" * 80)
    print("FCCS CACHE MEMBER SEARCH")
    print("=" * 80)
    print()
    
    # Search for E1, E2, E3 in entities
    print("Searching for entities: E1, E2, E3")
    print("-" * 80)
    entity_results = search_entity_cache(["E1", "E2", "E3"])
    
    if entity_results:
        for term, matches in entity_results.items():
            print(f"\nFound {len(matches)} match(es) for '{term}':")
            for match in matches:
                print(f"  - {match['name']:40s} (Parent: {match['parent']:30s}, Type: {match['type']})")
                if match['alias']:
                    print(f"    Alias: {match['alias']}")
    else:
        print("  [NOT FOUND] E1, E2, E3 do not exist in entity cache")
        print()
        print("  Searching for similar patterns (Letter + Number)...")
        # Find entities with pattern E + number
        all_entities = list_all_entities(limit=1000)
        pattern_matches = [e for e in all_entities if len(e) <= 5 and e[0].isalpha() and e[1:].isdigit()]
        if pattern_matches:
            print(f"  Found {len(pattern_matches)} entities with similar pattern:")
            for match in pattern_matches[:20]:  # Show first 20
                print(f"    - {match}")
            if len(pattern_matches) > 20:
                print(f"    ... and {len(pattern_matches) - 20} more")
    
    print()
    print("=" * 80)
    
    # Search for A1, A2, A3 in accounts
    print("Searching for accounts: A1, A2, A3")
    print("-" * 80)
    account_results = search_account_cache(["A1", "A2", "A3"])
    
    if account_results:
        for term, matches in account_results.items():
            print(f"\nFound {len(matches)} match(es) for '{term}':")
            for match in matches:
                print(f"  - {match['name']:40s} (Parent: {match['parent']:30s}, Type: {match['type']})")
                if match['alias']:
                    print(f"    Alias: {match['alias']}")
    else:
        print("  [NOT FOUND] A1, A2, A3 do not exist in account cache")
        print()
        print("  Searching for similar patterns (Letter + Number)...")
        # Find accounts with pattern A + number
        all_accounts = list_all_accounts(limit=1000)
        pattern_matches = [a for a in all_accounts if len(a) <= 5 and a[0].isalpha() and a[1:].isdigit()]
        if pattern_matches:
            print(f"  Found {len(pattern_matches)} accounts with similar pattern:")
            for match in pattern_matches[:20]:  # Show first 20
                print(f"    - {match}")
            if len(pattern_matches) > 20:
                print(f"    ... and {len(pattern_matches) - 20} more")
    
    print()
    print("=" * 80)
    print()
    
    # Show some example entities and accounts that could be used
    print("EXAMPLE VALID MEMBERS (for reference):")
    print("-" * 80)
    print("\nSample Entities:")
    sample_entities = list_all_entities(limit=10)
    for i, entity in enumerate(sample_entities, 1):
        print(f"  {i:2d}. {entity}")
    
    print("\nSample Accounts:")
    sample_accounts = list_all_accounts(limit=10)
    for i, account in enumerate(sample_accounts, 1):
        print(f"  {i:2d}. {account}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

