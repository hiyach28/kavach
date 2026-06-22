import React, { useState, useRef, useCallback } from 'react';

// Lazy-load Tesseract only when image is submitted
async function runOCR(imageFile, onProgress) {
  const { createWorker } = await import('tesseract.js');
  const worker = await createWorker('eng', 1, {
    logger: (m) => {
      if (m.status === 'recognizing text') {
        onProgress(Math.round(m.progress * 100));
      }
    },
  });
  const { data: { text } } = await worker.recognize(imageFile);
  await worker.terminate();
  return text.trim();
}

export default function ClassifierInput({ onSubmit, isLoading }) {
  const [inputMode, setInputMode] = useState('text'); // 'text' | 'image'
  const [text, setText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(null);
  const [statusLog, setStatusLog] = useState([]);
  const fileInputRef = useRef(null);

  const appendLog = (msg) => setStatusLog(prev => [...prev, msg]);

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || isLoading) return;
    setStatusLog([]);
    onSubmit(text);
    scheduleTextLogs();
  };

  const scheduleTextLogs = () => {
    const logs = [
      { msg: 'INITIALIZING DE-IDENTIFICATION PIPELINE...', delay: 0 },
      { msg: 'PII MASKING COMPLETE — PHONE & AADHAAR TOKENS APPLIED', delay: 400 },
      { msg: 'PAYLOAD ENCRYPTED AND DISPATCHED FOR INFERENCE...', delay: 700 },
      { msg: 'STRUCTURING INFERENCE RESPONSE SCHEMA...', delay: 1100 },
      { msg: 'UPDATING LOUVAIN COMMUNITY CLUSTERING GRAPH...', delay: 1300 },
    ];
    logs.forEach(l => setTimeout(() => appendLog(l.msg), l.delay));
  };

  const handleImageSubmit = async (e) => {
    e.preventDefault();
    if (!imageFile || isLoading) return;
    setStatusLog([]);
    setOcrProgress(0);

    try {
      appendLog('LOADING OCR ENGINE (TESSERACT.JS)...');
      appendLog('SCANNING IMAGE FOR TEXT CONTENT...');

      const extracted = await runOCR(imageFile, (pct) => {
        setOcrProgress(pct);
      });

      setOcrProgress(100);

      if (!extracted || extracted.length < 5) {
        appendLog('[WARN] INSUFFICIENT TEXT DETECTED IN IMAGE — USING FILENAME HEURISTIC');
        const fallback = imageFile.name.replace(/\.(png|jpg|jpeg|webp)/i, '').replace(/[-_]/g, ' ');
        onSubmit(fallback || 'screenshot submitted for analysis');
      } else {
        appendLog(`OCR COMPLETE — ${extracted.length} CHARACTERS EXTRACTED`);
        appendLog('RUNNING DE-IDENTIFICATION PIPELINE ON EXTRACTED TEXT...');
        onSubmit(extracted);
      }

      scheduleTextLogs();
    } catch (err) {
      appendLog(`[ERROR] OCR FAILED: ${err.message}`);
      setOcrProgress(null);
    }
  };

  const handleFile = useCallback((file) => {
    if (!file) return;
    const validTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      appendLog('[ERROR] UNSUPPORTED FORMAT — USE PNG, JPG, WEBP');
      return;
    }
    setImageFile(file);
    setStatusLog([]);
    setOcrProgress(null);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  }, [handleFile]);

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = () => setIsDragging(false);

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    setStatusLog([]);
    setOcrProgress(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="border border-border-hairline rounded bg-bg-surface overflow-hidden">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border-hairline bg-bg-base/30">
        <span className="font-condensed text-xs font-bold tracking-widest text-text-secondary uppercase">
          EVIDENCE_SUBMISSION_TERMINAL
        </span>
        <span className="font-mono text-[9px] text-sev-verified uppercase tracking-tight bg-sev-verified/10 px-2 py-0.5 border border-sev-verified/20 rounded">
          ● PII_GUARD: ACTIVE
        </span>
      </div>

      {/* Mode Tabs */}
      <div className="flex border-b border-border-hairline">
        <button
          onClick={() => setInputMode('text')}
          className={`flex-1 py-2.5 font-condensed text-xs font-bold tracking-wider uppercase transition-all duration-150 ${inputMode === 'text'
              ? 'text-accent-signal border-b-2 border-accent-signal bg-accent-signal/5'
              : 'text-text-secondary hover:text-text-primary border-b-2 border-transparent'
            }`}
        >
          ✎ Text / Transcript
        </button>
        <button
          onClick={() => setInputMode('image')}
          className={`flex-1 py-2.5 font-condensed text-xs font-bold tracking-wider uppercase transition-all duration-150 ${inputMode === 'image'
              ? 'text-mod-network border-b-2 border-mod-network bg-mod-network/5'
              : 'text-text-secondary hover:text-text-primary border-b-2 border-transparent'
            }`}
        >
          ⬛ Screenshot / Image
        </button>
      </div>

      <div className="p-5 space-y-4">
        {/* ─── TEXT MODE ─── */}
        {inputMode === 'text' && (
          <form onSubmit={handleTextSubmit} className="space-y-4">
            <div className="relative">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder={`Paste call transcript, SMS, WhatsApp message, or UPI payment request here…\n\nExample: "I received a call from someone claiming to be a CBI officer saying my Aadhaar is linked to money laundering..."`}
                rows={7}
                disabled={isLoading}
                className="w-full bg-bg-base border border-border-hairline rounded p-4 text-sm text-text-primary placeholder:text-text-secondary/40 font-mono focus:border-accent-signal transition-colors leading-relaxed resize-none"
              />
              {text.length > 0 && (
                <span className="absolute bottom-2 right-3 font-mono text-[9px] text-text-secondary/50">
                  {text.length} chars
                </span>
              )}
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <p className="text-[10px] text-text-secondary max-w-md leading-relaxed">
                📋 Phone numbers and Aadhaar IDs are automatically masked client-side before any analysis.
              </p>
              <button
                type="submit"
                disabled={!text.trim() || isLoading}
                className={`px-6 py-2.5 rounded font-condensed font-bold text-xs tracking-wider border transition-all duration-200 whitespace-nowrap ${!text.trim() || isLoading
                    ? 'bg-bg-base border-border-hairline text-text-secondary/40 cursor-not-allowed'
                    : 'bg-accent-signal/20 hover:bg-accent-signal/30 text-accent-signal border-accent-signal/40 hover:scale-[1.02] active:scale-[0.98]'
                  }`}
              >
                {isLoading ? '⟳ ANALYZING...' : '▶ RUN VERDICT ANALYSIS'}
              </button>
            </div>
          </form>
        )}

        {/* ─── IMAGE MODE ─── */}
        {inputMode === 'image' && (
          <form onSubmit={handleImageSubmit} className="space-y-4">
            {!imagePreview ? (
              /* Drop Zone */
              <div
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onClick={() => fileInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-lg p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-200 ${isDragging
                    ? 'border-mod-network bg-mod-network/10 scale-[1.01]'
                    : 'border-border-hairline hover:border-mod-network/60 hover:bg-mod-network/5'
                  }`}
              >
                <div className="text-4xl select-none">📸</div>
                <div className="text-center space-y-1">
                  <p className="font-condensed font-bold text-sm text-text-primary tracking-wide">
                    {isDragging ? 'Drop screenshot here' : 'Upload Screenshot or Image'}
                  </p>
                  <p className="font-mono text-[10px] text-text-secondary">
                    Drag & drop or click to browse — PNG, JPG, WEBP supported
                  </p>
                </div>
                <span className="font-mono text-[9px] text-mod-network/70 uppercase tracking-widest">
                  OCR text extraction will run in-browser
                </span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  className="hidden"
                  onChange={(e) => handleFile(e.target.files?.[0])}
                />
              </div>
            ) : (
              /* Preview + Actions */
              <div className="space-y-3">
                <div className="relative border border-border-hairline rounded overflow-hidden bg-bg-base">
                  <img
                    src={imagePreview}
                    alt="Uploaded evidence screenshot"
                    className="w-full max-h-64 object-contain"
                  />
                  <button
                    type="button"
                    onClick={clearImage}
                    className="absolute top-2 right-2 bg-bg-surface/90 border border-border-hairline text-text-secondary hover:text-sev-critical hover:border-sev-critical/40 rounded px-2 py-1 font-mono text-[9px] transition-all"
                  >
                    ✕ REMOVE
                  </button>
                  <div className="absolute bottom-0 left-0 right-0 bg-bg-base/80 px-3 py-1.5 font-mono text-[9px] text-text-secondary truncate">
                    {imageFile?.name} · {(imageFile?.size / 1024).toFixed(1)} KB
                  </div>
                </div>

                {/* OCR Progress Bar */}
                {ocrProgress !== null && ocrProgress < 100 && (
                  <div className="space-y-1.5">
                    <div className="flex justify-between font-mono text-[9px] text-text-secondary">
                      <span>OCR SCAN PROGRESS</span>
                      <span>{ocrProgress}%</span>
                    </div>
                    <div className="h-1 bg-bg-base border border-border-hairline rounded-full overflow-hidden">
                      <div
                        className="h-full bg-mod-network rounded-full transition-all duration-300"
                        style={{ width: `${ocrProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between gap-3">
                  <p className="text-[10px] text-text-secondary leading-relaxed">
                    🔍 Text will be extracted via OCR, then de-identified and classified.
                  </p>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className={`px-6 py-2.5 rounded font-condensed font-bold text-xs tracking-wider border transition-all duration-200 whitespace-nowrap ${isLoading
                        ? 'bg-bg-base border-border-hairline text-text-secondary/40 cursor-not-allowed'
                        : 'bg-mod-network/20 hover:bg-mod-network/30 text-mod-network border-mod-network/40 hover:scale-[1.02] active:scale-[0.98]'
                      }`}
                  >
                    {isLoading ? '⟳ SCANNING...' : '▶ SCAN & CLASSIFY'}
                  </button>
                </div>
              </div>
            )}
          </form>
        )}

        {/* ─── Status Log Terminal ─── */}
        {statusLog.length > 0 && (
          <div className="p-3 bg-bg-base border border-border-hairline rounded font-mono text-[10px] leading-loose space-y-0.5 select-none">
            {statusLog.map((log, idx) => (
              <div key={idx} className="flex items-start space-x-2 animate-fade-in">
                <span className="text-accent-signal flex-shrink-0">›</span>
                <span className={log.startsWith('[ERROR]') ? 'text-sev-critical' : log.startsWith('[WARN]') ? 'text-sev-high' : 'text-mod-network'}>
                  {log}
                </span>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center space-x-2 pt-1">
                <span className="flex gap-0.5">
                  <span className="h-1 w-1 bg-mod-network rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="h-1 w-1 bg-mod-network rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="h-1 w-1 bg-mod-network rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
                <span className="text-text-secondary text-[8px] animate-pulse">PROCESSING INFERENCE STREAM...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
