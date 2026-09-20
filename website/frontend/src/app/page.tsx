'use client';
import { useState, useEffect } from 'react';
import { Download, Upload, ExternalLink, Database, Sliders, FileCode, Check, Award, FileText, Copy } from 'lucide-react';
import Image from 'next/image';

function GitHubIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
    </svg>
  );
}

export default function Home() {
  const [schemas, setSchemas] = useState<string[]>([]);
  const [selectedSchema, setSelectedSchema] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [copied, setCopied] = useState(false);
  const [categories, setCategories] = useState({
    aliases: true,
    directives: true,
    external_fragments: true,
    filters: true,
    inline_fragments: true,
    pagination: true,
    mutations: true,
  });
  const [count, setCount] = useState(3);
  const [maxHops, setMaxHops] = useState(2);
  const [loading, setLoading] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/schemas`)
      .then((res) => res.json())
      .then((data) => setSchemas(data.schemas || []))
      .catch((err) => console.error(err));
  }, [API_BASE_URL]);

  const handleCategoryChange = (key: keyof typeof categories) => {
    setCategories((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData();
    if (selectedSchema) formData.append('schema_names', selectedSchema);
    if (uploadedFile) formData.append('schema_file', uploadedFile);
    
    const activeCategories = Object.entries(categories)
      .filter(([_, active]) => active)
      .map(([key]) => key)
      .join(',');
    
    formData.append('categories', activeCategories);
    formData.append('count', count.toString());
    formData.append('max_hops', maxHops.toString());

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate`, {
        method: 'POST',
        body: formData,
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'autographql_dataset.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        alert('Failed to generate dataset.');
      }
    } catch (err) {
      console.error(err);
      alert('Error generating dataset.');
    } finally {
      setLoading(false);
    }
  };

  const handleDatasetDownload = (type: 'train' | 'test') => {
    window.location.href = `${API_BASE_URL}/api/datasets/${type}`;
  };

  const bibtexText = `@inproceedings{autographql2026,
  title={-},
  author={-},
  booktitle={-},
  year={2026}
}`;

  const handleCopyBibtex = () => {
    navigator.clipboard.writeText(bibtexText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased selection:bg-blue-100">
      {/* Navigation Header */}
      <nav className="bg-white border-b border-blue-100 sticky top-0 z-50 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-12 h-16 flex items-center justify-between gap-2">
          <a href="#" className="text-base sm:text-xl font-bold tracking-tight text-blue-950 flex items-center gap-2 shrink-0">
            <Image src="/favicon.ico" alt="AutoGraphQL Logo" width={24} height={24} className="w-5 h-5 sm:w-6 sm:h-6 object-contain" />
            <span>AutoGraphQL</span>
          </a>
          <div className="flex items-center gap-3 sm:gap-6 text-xs sm:text-sm font-medium text-slate-600 shrink-0">
            <a 
              href="/autographql.pdf" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-1 sm:gap-1.5 hover:text-blue-700 transition-colors"
            >
              <FileText size={15} className="text-blue-700" />
              <span>Paper</span>
              <ExternalLink size={11} className="text-slate-400 hidden sm:inline" />
            </a>
            <a 
              href="https://nl2graphql-bench.github.io/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-1 sm:gap-1.5 hover:text-blue-700 transition-colors"
            >
              <Award size={15} className="text-blue-700" />
              <span>Leaderboard</span>
              <ExternalLink size={11} className="text-slate-400 hidden sm:inline" />
            </a>
            <a 
              href="https://github.com/keya-x/autographql" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-1 sm:gap-1.5 hover:text-blue-700 transition-colors"
            >
              <GitHubIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-700" />
              <span>Code</span>
              <ExternalLink size={11} className="text-slate-400 hidden sm:inline" />
            </a>
          </div>
        </div>
      </nav>

      {/* Hero / Paper Header */}
      <header className="bg-white border-b border-blue-100 py-12 px-6 sm:px-12">
        <div className="max-w-7xl mx-auto text-center space-y-4">
          <div>
            <span className="text-xs font-semibold text-slate-600 tracking-wide uppercase">
              Accepted at EMNLP 2026 (Industry Track)
            </span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-blue-950 tracking-tight leading-tight max-w-5xl mx-auto">
            AutoGraphQL: A Bring-Your-Own-Schema Framework for Adapting Open-Weight LLMs to GraphQL APIs
          </h1>

          {/* Academic Resource Links */}
          <div className="pt-2 flex flex-wrap justify-center gap-3">
            <a 
              href="/autographql.pdf" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center min-w-[130px] gap-2 px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium rounded shadow-xs transition-colors"
            >
              <FileText size={16} />
              <span>Paper</span>
              <ExternalLink size={12} className="opacity-80" />
            </a>
            <a 
              href="https://github.com/keya-x/autographql" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center min-w-[130px] gap-2 px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium rounded shadow-xs transition-colors"
            >
              <GitHubIcon className="w-4 h-4" />
              <span>Repository</span>
              <ExternalLink size={12} className="opacity-80" />
            </a>
            <a 
              href="https://nl2graphql-bench.github.io/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center min-w-[130px] gap-2 px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium rounded shadow-xs transition-colors"
            >
              <Award size={16} />
              <span>Leaderboard</span>
              <ExternalLink size={12} className="opacity-80" />
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 sm:px-12 py-12 space-y-10">
        {/* Abstract / Overview */}
        <section className="bg-white rounded-lg p-6 sm:p-8 border border-blue-100 shadow-xs space-y-4">
          <h2 className="text-xl font-bold text-blue-950 border-b border-blue-100 pb-3">Abstract</h2>
          <p className="text-slate-700 leading-relaxed text-sm sm:text-base">
            AutoGraphQL is a systematic, schema-driven framework for synthesizing GraphQL query datasets directly from GraphQL SDL schemas. It supports a broad range of GraphQL constructs, including fragments, inline fragments, directives, filters, pagination, aliases, and mutations, enabling the automated creation of diverse, executable datasets for fine-tuning LLMs and adapting them to domain or enterprise-specific schemas.
          </p>
        </section>

        {/* Official Datasets Section */}
        <section className="bg-white rounded-lg p-6 sm:p-8 border border-blue-100 shadow-xs space-y-6">
          <div className="flex items-center gap-3 border-b border-blue-100 pb-3">
            <Database size={20} className="text-blue-700" />
            <h2 className="text-xl font-bold text-blue-950">Official Datasets</h2>
          </div>

          <p className="text-slate-700 text-sm sm:text-base">
            Download our NL2GraphQL corpus used for fine-tuning and benchmarking in the paper.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-5 border border-blue-100 rounded-md bg-blue-50/30 flex flex-col justify-between space-y-4">
              <h3 className="font-semibold text-blue-950 text-base">Training Dataset</h3>
              <button
                onClick={() => handleDatasetDownload('train')}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium rounded transition-colors shadow-xs"
              >
                <Download size={16} />
                <span>Download Training Dataset</span>
              </button>
            </div>

            <div className="p-5 border border-blue-100 rounded-md bg-blue-50/30 flex flex-col justify-between space-y-4">
              <h3 className="font-semibold text-blue-950 text-base">Testing Dataset</h3>
              <button
                onClick={() => handleDatasetDownload('test')}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium rounded transition-colors shadow-xs"
              >
                <Download size={16} />
                <span>Download Testing Dataset</span>
              </button>
            </div>
          </div>
        </section>

        {/* Dataset Generator Tool */}
        <section className="bg-white rounded-lg p-6 sm:p-8 border border-blue-100 shadow-xs space-y-6">
          <div className="flex items-center gap-3 border-b border-blue-100 pb-3">
            <Sliders size={20} className="text-blue-700" />
            <h2 className="text-xl font-bold text-blue-950">Synthetic Dataset Generator</h2>
          </div>

          <form onSubmit={handleGenerate} className="space-y-8">
            {/* Step 1: Schema Selection */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-blue-950">
                1. Select Target Schema
              </label>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-slate-600">Choose from Schemas</span>
                  <select 
                    value={selectedSchema} 
                    onChange={(e) => { setSelectedSchema(e.target.value); setUploadedFile(null); }}
                    className="w-full p-2.5 text-sm border border-slate-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700"
                  >
                    <option value="">-- Select Schema --</option>
                    {schemas.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-slate-600">Or Upload Custom Schema (.graphql)</span>
                  <div className="relative">
                    <input 
                      type="file" 
                      accept=".graphql"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          setUploadedFile(e.target.files[0]);
                          setSelectedSchema('');
                        }
                      }}
                      className="hidden"
                      id="file-upload"
                    />
                    <label 
                      htmlFor="file-upload"
                      className={`flex items-center justify-center gap-2 w-full p-2.5 text-sm border rounded cursor-pointer transition-colors ${uploadedFile ? 'border-blue-700 bg-blue-50 text-blue-950 font-medium' : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'}`}
                    >
                      {uploadedFile ? <Check size={16} className="text-blue-700" /> : <Upload size={16} />}
                      <span className="truncate">{uploadedFile ? uploadedFile.name : 'Upload .graphql file'}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 2: Query Categories */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-blue-950">
                2. Select Query Categories
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
                {Object.entries(categories).map(([key, active]) => (
                  <button 
                    type="button"
                    key={key} 
                    onClick={() => handleCategoryChange(key as keyof typeof categories)}
                    className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded border text-xs font-medium cursor-pointer transition-colors select-none ${active ? 'border-blue-700 bg-blue-700 text-white shadow-xs' : 'border-slate-300 bg-white text-slate-700 hover:border-blue-300 hover:bg-slate-50'}`}
                  >
                    <span className={`w-3.5 h-3.5 rounded flex items-center justify-center border text-[10px] ${active ? 'border-white bg-white text-blue-700 font-bold' : 'border-slate-400 bg-white'}`}>
                      {active ? '✓' : ''}
                    </span>
                    <span className="capitalize truncate">{key.replace('_', ' ')}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Step 3: Parameters */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-blue-950">
                3. Generation Parameters
              </label>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-slate-600">Queries per Category</span>
                  <input 
                    type="number" 
                    min="1" 
                    value={count} 
                    onChange={(e) => setCount(parseInt(e.target.value))}
                    className="w-full p-2.5 text-sm border border-slate-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700"
                  />
                </div>
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-slate-600">Maximum Query Depth</span>
                  <input 
                    type="number" 
                    min="1" 
                    max="10"
                    value={maxHops} 
                    onChange={(e) => setMaxHops(parseInt(e.target.value))}
                    className="w-full p-2.5 text-sm border border-slate-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700"
                  />
                </div>
              </div>
            </div>

            {/* Submit Action */}
            <div className="pt-4 border-t border-blue-100">
              <button 
                type="submit" 
                disabled={loading || (!selectedSchema && !uploadedFile)}
                className={`w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded text-sm font-semibold transition-colors ${loading || (!selectedSchema && !uploadedFile) ? 'bg-slate-200 text-slate-400 cursor-not-allowed' : 'bg-blue-700 hover:bg-blue-800 text-white shadow-xs'}`}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Synthesizing Dataset...</span>
                  </>
                ) : (
                  <>
                    <FileCode size={16} />
                    <span>Generate & Download Excel Dataset</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        {/* Citation Template Section */}
        <section className="bg-white rounded-lg p-6 sm:p-8 border border-blue-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-blue-100 pb-3">
            <h2 className="text-xl font-bold text-blue-950">Citation</h2>
            <button
              onClick={handleCopyBibtex}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
            >
              {copied ? <Check size={14} className="text-blue-700" /> : <Copy size={14} />}
              <span>{copied ? 'Copied!' : 'Copy BibTeX'}</span>
            </button>
          </div>
          <p className="text-slate-700 text-sm">
            Please cite the repo if you think our work is helpful to you.
          </p>
          <pre className="p-4 bg-slate-900 text-slate-100 rounded-md text-xs font-mono overflow-x-auto leading-relaxed">
            {bibtexText}
          </pre>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-blue-100 bg-white py-6">
        <div className="max-w-7xl mx-auto px-6 sm:px-12 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-medium text-slate-600">
          <span className="font-semibold text-blue-950">AutoGraphQL</span>
          <div className="flex items-center gap-6">
            <a 
              href="/autographql.pdf" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-blue-700 transition-colors"
            >
              Paper
            </a>
            <a 
              href="https://github.com/keya-x/autographql" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-blue-700 transition-colors"
            >
              Repository
            </a>
            <a 
              href="https://nl2graphql-bench.github.io/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-blue-700 transition-colors"
            >
              Leaderboard
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
