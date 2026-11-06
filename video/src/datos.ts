// Los vídeos no inventan datos: leen el caso de muestra del producto y su motor de reglas.
// Si el producto cambia y el guion deja de ser cierto, el render falla aquí.
import {SAMPLE_NOW, SOLARIS_PACKS} from '../../product/lib/solaris-data';
import {evaluatePack} from '../../product/lib/rules-engine';
import {crossCheckFor, gapsFrom} from '../../product/lib/gaps';
import {NO_SIGNER_ROLE, roleBlockReason} from '../../product/lib/review-rules';

export const compras = SOLARIS_PACKS.compras;
// La misma fecha de muestra con la que evalúa la demo.
const resultados = evaluatePack(compras, {now: SAMPLE_NOW});
export const huecos = gapsFrom(compras, resultados);

const pares = huecos.open.map((g) => `${g.objectId}/${g.rule.code}`).sort().join(' ');
if (pares !== 'PC-0412/R-03 PC-0419/R-01 PC-0419/R-02') {
  throw new Error(`El motor ya no da los huecos del guion: ${pares}`);
}
if (huecos.pendingData[0]?.objectId !== 'FAC-2026-889') {
  throw new Error('El dato por validar del guion ha cambiado');
}

// STATUS.md (H7): los nombres de proveedor están sin comprobar en el registro mercantil.
// En vídeo solo salen sus identificadores.
export const sinProveedor = (s: string) =>
  s
    .replace('Suministros Industriales del Norte S.L. (PROV-018)', 'PROV-018')
    .replace('Logística y Embalajes Delta S.A. (PROV-024)', 'PROV-024');

const ROTULOS: Record<string, string> = {
  conforme: 'Conforme', incumplida: 'Incumplida', requiere_aprobacion: 'Requiere aprobación',
  candidato: 'Dato por validar', sin_evidencia: 'Falta evidencia', no_aplica: 'No evaluada',
};
export type Celda = {regla: string; estado: string; rotulo: string};
const celdas = (id: string): Celda[] =>
  ['R-01', 'R-02', 'R-03'].map((regla) => {
    const cruce = crossCheckFor(id, compras, resultados).find((x) => x.ruleCode === regla);
    if (!cruce) throw new Error(`Sin cruce ${id}/${regla}`);
    return {regla, estado: cruce.estado, rotulo: ROTULOS[cruce.estado]};
  });
export const matriz = [
  {id: 'PC-0412', detalle: '18.450,00 €', celdas: celdas('PC-0412')},
  {id: 'PC-0419', detalle: '9.200,00 €', celdas: celdas('PC-0419')},
];

const q = compras.questions;
export const pregunta = q[0].question;
export const respuesta = q[0].answerByLang.ES.leadSummary;
export const fundamento = q[0].answerByLang.ES.paragraphs[1].text;
export const preguntaSinFuente = q[2].question;
export const respuestaSinFuente = q[2].answerByLang.ES.leadSummary;
export const avisoSinFuente = q[2].answerByLang.ES.paragraphs[1].unverifiedWarning as string;

export const evPolitica = compras.evidences['EV-COMP-01'];
export const evCertificado = compras.evidences['EV-COMP-03'];
export const evFactura = compras.evidences['EV-COMP-04'];
export const documentos = Object.values(compras.evidences);

export const revision = compras.reviewQueue[0];
export const borrador = sinProveedor(revision.proposedDraft);
export const rolSinFirma = NO_SIGNER_ROLE;
export const motivoBloqueo = roleBlockReason(NO_SIGNER_ROLE, revision) as string;
