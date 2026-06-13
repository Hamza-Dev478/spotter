import { useRef, useState } from "react";
import type { DailyLog, LogMeta } from "../../types/trip";
import { DriversDailyLogSheet } from "./DriversDailyLogSheet";

interface Props {
  logs: DailyLog[];
  meta?: LogMeta;
}

async function captureElement(el: HTMLElement) {
  const html2canvas = (await import("html2canvas")).default;
  return html2canvas(el, { scale: 2, backgroundColor: "#ffffff", useCORS: true, logging: false });
}

/** Robust cross-browser file download via a blob object URL. */
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

export function DailyLogs({ logs, meta }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState<null | "pdf" | "png">(null);

  const exportPDF = async () => {
    if (!containerRef.current) return;
    setBusy("pdf");
    try {
      const { jsPDF } = await import("jspdf");
      const sheets = Array.from(
        containerRef.current.querySelectorAll<HTMLElement>("[data-log-sheet]"),
      );
      const pdf = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();

      for (let i = 0; i < sheets.length; i++) {
        const canvas = await captureElement(sheets[i]);
        const imgW = pageW - 40;
        const imgH = (canvas.height / canvas.width) * imgW;
        const y = Math.max(20, (pageH - imgH) / 2);
        if (i > 0) pdf.addPage();
        // JPEG keeps the line-art crisp while keeping the file small.
        pdf.addImage(canvas.toDataURL("image/jpeg", 0.92), "JPEG", 20, y, imgW, imgH);
      }
      downloadBlob(pdf.output("blob"), "eld-daily-logs.pdf");
    } finally {
      setBusy(null);
    }
  };

  const exportPNG = async () => {
    if (!containerRef.current) return;
    setBusy("png");
    try {
      const canvas = await captureElement(containerRef.current);
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/png"));
      if (blob) downloadBlob(blob, "eld-daily-logs.png");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <div className="logs-head" style={{ marginBottom: 12 }}>
        <div className="card-head" style={{ padding: 0 }}>
          <span className="icon">📋</span>
          <div>
            <h2>Daily log sheets</h2>
            <div className="sub">
              {logs.length} sheet{logs.length === 1 ? "" : "s"} · drawn on the FMCSA grid
            </div>
          </div>
        </div>
        <div className="actions">
          <button className="btn btn-ghost btn-sm" onClick={exportPNG} disabled={busy !== null}>
            {busy === "png" ? <span className="spinner dark" /> : "⬇︎"} PNG
          </button>
          <button className="btn btn-ghost btn-sm" onClick={exportPDF} disabled={busy !== null}>
            {busy === "pdf" ? <span className="spinner dark" /> : "⬇︎"} PDF
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => window.print()} disabled={busy !== null}>
            🖨︎ Print
          </button>
        </div>
      </div>

      <div ref={containerRef}>
        {logs.map((log, i) => (
          <DriversDailyLogSheet
            key={log.date}
            log={log}
            pageNumber={i + 1}
            totalPages={logs.length}
            meta={meta}
          />
        ))}
      </div>
    </div>
  );
}
