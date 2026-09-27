"use client";

import Link from "next/link";
import { useCallback, useEffect, useId, useRef, useState, type DragEvent } from "react";

import { AiLabel } from "@/components/notices";
import { api } from "@/lib/api";
import {
  ApiError,
  type CaseListItem,
  type CaseView,
  type ComplaintParsed,
  type ProgressEvent,
} from "@/lib/api-client";
import { watchCase } from "@/lib/case-watch";
import {
  checkFile,
  formatElapsed,
  injectionNotice,
  isTerminal,
  otherWarnings,
  previewRows,
  progressAnnouncement,
  reviewNotice,
  statusLabel,
  stepsFor,
} from "@/lib/inbox";

import { CaseTable } from "./CaseTable";
import { ProgressSteps } from "./ProgressSteps";
import { InjectionBanner, ReviewNote } from "./SecurityNotices";

type ListState =
  | { status: "ok"; items: CaseListItem[] }
  | { status: "error"; message: string; forbidden: boolean };

type Phase =
  | { kind: "idle" }
  | { kind: "parsing"; file: File }
  | { kind: "preview"; file: File; parsed: ComplaintParsed }
  | { kind: "creating"; file: File; parsed: ComplaintParsed }
  | {
      kind: "watching";
      caseId: string;
      parsed: ComplaintParsed | null;
      startedAt: number;
      progress: ProgressEvent[];
      status: string;
      view: CaseView | null;
    };

function messageFor(e: unknown, action: string): string {
  if (e instanceof ApiError) {
    if (e.kind === "forbidden") return `Tu rol no puede ${action}. ${e.userMessage}`;
    if (e.kind === "conflict") return `Conflicto: ${e.userMessage}`;
    return e.userMessage;
  }
  return "Se ha producido un error inesperado.";
}

export default function InboxClient({ initial }: { initial: ListState }) {
  const [list, setList] = useState<ListState>(initial);
  const [loadingList, setLoadingList] = useState(false);
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  const inputId = useId();
  const hintId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const previewRef = useRef<HTMLHeadingElement>(null);
  const progressRef = useRef<HTMLHeadingElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);
  const parseCtrl = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    setLoadingList(true);
    try {
      const page = await api.cases();
      setList({ status: "ok", items: page.items });
    } catch (e) {
      setList({
        status: "error",
        message: messageFor(e, "ver los casos"),
        forbidden: e instanceof ApiError && e.kind === "forbidden",
      });
    } finally {
      setLoadingList(false);
    }
  }, []);

  // Foco en el bloque nuevo para teclado y lector de pantalla.
  const phaseKind = phase.kind;
  useEffect(() => {
    if (phaseKind === "preview") previewRef.current?.focus();
    if (phaseKind === "watching") progressRef.current?.focus();
  }, [phaseKind]);
  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);

  // Seguimiento del caso (SSE con polling de respaldo).
  const watchingId = phase.kind === "watching" ? phase.caseId : null;
  useEffect(() => {
    if (!watchingId) return;
    const stop = watchCase(watchingId, { getCase: api.getCase }, {
      onUpdate: (u) => {
        setPhase((p) => (p.kind === "watching" && p.caseId === watchingId
          ? { ...p, progress: u.progress, status: u.status, view: u.view ?? p.view }
          : p));
        // Al terminar, la bandeja se recarga para que aparezca el caso con su estado.
        if (u.view && isTerminal(u.status)) void refresh();
      },
      onError: (e) => setError(messageFor(e, "ver el caso")),
    });
    return stop;
  }, [watchingId, refresh]);

  // Cronómetro visible mientras genera (R-L01-2).
  const running = phase.kind === "watching" && !isTerminal(phase.status);
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [running]);

  useEffect(() => () => parseCtrl.current?.abort(), []);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setError(null);
    const bad = checkFile(file);
    if (bad) {
      setError(bad);
      return;
    }
    parseCtrl.current?.abort();
    const ctrl = new AbortController();
    parseCtrl.current = ctrl;
    setPhase({ kind: "parsing", file });
    try {
      const parsed = await api.parseComplaint(file, ctrl.signal);
      setPhase({ kind: "preview", file, parsed });
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setPhase({ kind: "idle" });
      setError(messageFor(e, "subir reclamaciones"));
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function generate() {
    if (phase.kind !== "preview") return;
    const { file, parsed } = phase;
    setError(null);
    setPhase({ kind: "creating", file, parsed });
    try {
      const created = await api.createCase(file);
      const startedAt = Date.now();
      setNow(startedAt);
      setPhase({
        kind: "watching", caseId: created.case_id, parsed, startedAt, progress: [],
        status: "drafting", view: null,
      });
      void refresh();
    } catch (e) {
      setPhase({ kind: "preview", file, parsed });
      setError(messageFor(e, "crear casos 8D"));
    }
  }

  function reset() {
    parseCtrl.current?.abort();
    setError(null);
    setPhase({ kind: "idle" });
  }

  const busy = phase.kind === "parsing" || phase.kind === "creating" ||
    (phase.kind === "watching" && !isTerminal(phase.status));

  function onDrop(ev: DragEvent<HTMLDivElement>) {
    ev.preventDefault();
    setDragging(false);
    if (busy) return;
    void handleFile(ev.dataTransfer.files?.[0]);
  }

  // --- avisos de seguridad del documento actual --------------------------------------------
  const secSource = phase.kind === "watching" && phase.view
    ? { injection_suspected: phase.view.complaint?.injection_suspected,
        warnings: phase.view.warnings }
    : phase.kind === "preview" || phase.kind === "creating" || phase.kind === "watching"
      ? phase.parsed
      : null;
  const injection = secSource ? injectionNotice(secSource) : null;
  const review = secSource ? reviewNotice(secSource.warnings) : null;
  const complaintId = phase.kind === "preview" || phase.kind === "creating"
    ? phase.parsed.complaint_id
    : phase.kind === "watching" ? (phase.view?.complaint_id ?? phase.parsed?.complaint_id) : null;

  const steps = phase.kind === "watching" ? stepsFor(phase.progress, phase.status) : [];
  const elapsed = phase.kind === "watching"
    ? (isTerminal(phase.status) && phase.view?.elapsed_s != null
      ? phase.view.elapsed_s
      : (now - phase.startedAt) / 1000)
    : 0;
  const announce = phase.kind === "parsing" ? "Leyendo la reclamación…"
    : phase.kind === "preview" ? "Campos extraídos. Revisa la vista previa."
    : phase.kind === "creating" ? "Creando el caso 8D…"
    : phase.kind === "watching" ? progressAnnouncement(steps, phase.status)
    : "";

  return (
    <>
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {announce}
      </div>

      {injection && <InjectionBanner notice={injection} complaintId={complaintId} />}
      {review && <ReviewNote notice={review} />}

      <div className="grid g2">
        <section className="card" aria-labelledby="casos-titulo">
          <div className="row between">
            <h2 id="casos-titulo">Casos 8D</h2>
            <button type="button" className="btn" onClick={() => void refresh()}
                    disabled={loadingList} aria-busy={loadingList}>
              {loadingList ? "Actualizando…" : "Actualizar"}
            </button>
          </div>
          {list.status === "error" ? (
            <div className={`alert ${list.forbidden ? "a-bad" : "a-warn"}`} role="alert">
              {list.forbidden ? <b>No tienes permiso para ver los casos 8D. </b> : null}
              {list.message}
            </div>
          ) : list.items.length === 0 ? (
            <p className="empty">
              Todavía no hay casos. Sube la reclamación del cliente (PDF o correo .eml) para
              generar el primer borrador 8D.
            </p>
          ) : (
            <CaseTable items={list.items} />
          )}
        </section>

        <section className="card" aria-labelledby="nueva-titulo">
          <h2 id="nueva-titulo">Nueva reclamación</h2>
          <div
            className={`drop${dragging ? " over" : ""}${busy ? " busy" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              if (!busy) setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            data-testid="dropzone"
          >
            <p>Arrastra aquí el PDF o el correo (.eml) del cliente, o</p>
            <label htmlFor={inputId} className="btn primary">Elegir fichero</label>
            <input
              ref={inputRef}
              id={inputId}
              type="file"
              className="visually-hidden"
              accept=".pdf,.eml,application/pdf,message/rfc822"
              aria-describedby={hintId}
              disabled={busy}
              onChange={(e) => void handleFile(e.target.files?.[0])}
            />
            <p id={hintId} className="note">
              Un fichero .pdf o .eml de hasta 10 MB. Su contenido se trata como dato del cliente,
              nunca como instrucciones.
            </p>
          </div>

          {error && (
            <div className="alert a-bad" role="alert" tabIndex={-1} ref={errorRef}>
              {error}
            </div>
          )}

          {phase.kind === "parsing" && (
            <p className="loading" aria-busy="true">
              Leyendo <span className="mono">{phase.file.name}</span>…
            </p>
          )}

          {(phase.kind === "preview" || phase.kind === "creating") && (
            <div className="preview">
              <h3 ref={previewRef} tabIndex={-1}>
                Campos extraídos · <span className="mono">{phase.file.name}</span> <AiLabel />
              </h3>
              <dl className="kv">
                {previewRows(phase.parsed).map((r) => (
                  <div key={r.label}>
                    <dt>{r.label}</dt>
                    <dd className={r.mono ? "mono" : undefined}>{r.value}</dd>
                  </div>
                ))}
              </dl>
              {otherWarnings(phase.parsed.warnings).map((m) => (
                <p key={m} className="note">⚠ {m}</p>
              ))}
              <div className="row">
                <button type="button" className="btn primary" onClick={() => void generate()}
                        disabled={phase.kind === "creating"}
                        aria-busy={phase.kind === "creating"}>
                  {phase.kind === "creating" ? "Creando el caso…" : "Generar borrador 8D"}
                </button>
                <button type="button" className="btn" onClick={reset}
                        disabled={phase.kind === "creating"}>
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {phase.kind === "watching" && (
            <div className="progress" data-testid="progress">
              <h3 ref={progressRef} tabIndex={-1}>
                Progreso · <span className="mono">{complaintId ?? "caso nuevo"}</span>{" "}
                <span className="tag" aria-label={`Tiempo: ${formatElapsed(elapsed)}`}>
                  {formatElapsed(elapsed)}
                </span>
              </h3>
              <ProgressSteps steps={steps} finalLabel="Borrador listo · pendiente de aprobación"
                             finalDone={phase.status === "pending_approval" ||
                               phase.status === "approved" || phase.status === "rejected"} />
              {isTerminal(phase.status) && (
                <div className="row">
                  {phase.status === "error" ? (
                    <p className="alert a-bad" role="alert">
                      No se ha podido generar el borrador.{" "}
                      {phase.view?.error ?? "Revisa la reclamación e inténtalo de nuevo."}
                    </p>
                  ) : (
                    <p>
                      <b>{statusLabel(phase.status)}.</b> El borrador D1–D4 <AiLabel /> necesita
                      revisión y aprobación humana antes de salir.
                    </p>
                  )}
                  <Link className="btn primary" href={`/casos/${phase.caseId}`}>
                    Abrir el caso
                  </Link>
                  <button type="button" className="btn" onClick={reset}>
                    Subir otra reclamación
                  </button>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
