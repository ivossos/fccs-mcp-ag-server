import React from 'react';
import { TrendingUp, DollarSign, Activity, PieChart } from 'lucide-react';

const DCFValuationReport = () => {
  const projections = [
    { year: 'FY26', fcf: 16.92, pv: 15.38, growth: '5%' },
    { year: 'FY27', fcf: 17.77, pv: 14.68, growth: '5%' },
    { year: 'FY28', fcf: 18.66, pv: 14.02, growth: '5%' },
    { year: 'FY29', fcf: 19.22, pv: 13.12, growth: '3%' },
    { year: 'FY30', fcf: 19.80, pv: 12.29, growth: '3%' },
  ];

  return (
    <div className="p-6 bg-slate-50 min-h-screen font-sans text-slate-900">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="mb-8 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold text-indigo-900">DCF Valuation Report</h1>
            <p className="text-slate-500">Target Date: June 2025 | Entity: VENTURI_SUPPLY</p>
          </div>
          <div className="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-full text-sm font-semibold border border-indigo-200">
            Valuation Method: Gordon Growth Model
          </div>
        </header>

        {/* Top Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center gap-3 mb-2 text-indigo-600">
              <DollarSign size={20} />
              <span className="text-sm font-medium uppercase tracking-wider">Enterprise Value</span>
            </div>
            <div className="text-2xl font-bold">$237.5M</div>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center gap-3 mb-2 text-emerald-600">
              <Activity size={20} />
              <span className="text-sm font-medium uppercase tracking-wider">Equity Value</span>
            </div>
            <div className="text-2xl font-bold">$238.3M</div>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center gap-3 mb-2 text-amber-600">
              <TrendingUp size={20} />
              <span className="text-sm font-medium uppercase tracking-wider">EV/EBITDA</span>
            </div>
            <div className="text-2xl font-bold">10.28x</div>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center gap-3 mb-2 text-rose-600">
              <PieChart size={20} />
              <span className="text-sm font-medium uppercase tracking-wider">WACC</span>
            </div>
            <div className="text-2xl font-bold">10.0%</div>
          </div>
        </div>

        {/* Projections Table */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
          <div className="p-5 border-b border-slate-100 bg-slate-50">
            <h2 className="font-bold text-slate-800 uppercase text-xs tracking-widest">5-Year Cash Flow Projections ($ Millions)</h2>
          </div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-slate-400 text-xs uppercase font-semibold">
                <th className="px-6 py-4">Fiscal Year</th>
                <th className="px-6 py-4">Projected Growth</th>
                <th className="px-6 py-4">Free Cash Flow (FCF)</th>
                <th className="px-6 py-4">Present Value (PV)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {projections.map((p) => (
                <tr key={p.year} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-bold text-indigo-900">{p.year}</td>
                  <td className="px-6 py-4 text-slate-600">{p.growth}</td>
                  <td className="px-6 py-4 text-slate-700 font-medium">${p.fcf}M</td>
                  <td className="px-6 py-4 text-indigo-600 font-semibold">${p.pv}M</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Sensitivity Analysis */}
        <div className="bg-indigo-900 rounded-xl shadow-lg p-6 text-white">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Activity size={20} className="text-indigo-300" />
            Sensitivity Analysis: Enterprise Value
          </h2>
          <div className="grid grid-cols-3 gap-6">
            <div className="border-l-2 border-indigo-700 pl-4">
              <p className="text-indigo-300 text-xs uppercase mb-1">Growth +0.5%</p>
              <p className="text-xl font-bold">$250.3M</p>
            </div>
            <div className="border-l-2 border-indigo-500 pl-4 bg-indigo-800 p-2 rounded">
              <p className="text-indigo-200 text-xs uppercase mb-1 font-bold italic underline">Base Case</p>
              <p className="text-xl font-bold underline italic">$237.5M</p>
            </div>
            <div className="border-l-2 border-indigo-700 pl-4">
              <p className="text-indigo-300 text-xs uppercase mb-1">Growth -0.5%</p>
              <p className="text-xl font-bold">$226.2M</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DCFValuationReport;



