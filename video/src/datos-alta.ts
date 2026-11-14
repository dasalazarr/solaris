// «Alta de cliente»: el proceso de la línea base de H03, creado desde la app sin programar.
// Definición y casos copiados del fixture de product/tests/process-cases.test.ts. Se validan y evalúan
// con las mismas funciones que usa el producto; si el resultado deja de ser el del guion, el render falla.
import {SAMPLE_NOW} from '../../product/lib/solaris-data';
import {blankDefinition, newProcessId, seedFromCases, type TestCase} from '../../product/lib/process-cases';
import {assemblePack, describeLogic, policyHash, validateDefinition, type ProcessDefinition} from '../../product/lib/process-definition';
import {evaluatePack} from '../../product/lib/rules-engine';
import {matrixFrom} from '../../product/lib/gaps';
import {roleBlockReason} from '../../product/lib/review-rules';

const id = newProcessId('Alta de cliente', [], 'r');

const borrador: ProcessDefinition = {
  ...blankDefinition(id, 'Alta de cliente', 'Comercial'),
  scope: 'Desde la solicitud de alta de un cliente hasta su activación para facturar.',
  roles: ['Comercial', 'Riesgos'],
  objectTypes: [
    {
      id: 'Cliente',
      label: 'Cliente',
      attributes: [
        {key: 'cif_verificado', label: 'CIF verificado', type: 'boolean'},
        {key: 'limite_credito', label: 'Límite de crédito', type: 'number'},
        {key: 'contrato_firmado', label: 'Fecha del contrato firmado', type: 'date'},
      ],
      relations: [],
    },
  ],
  rules: [
    {id: 'r1', code: 'R-01', name: 'CIF verificado', description: 'No se da de alta a un cliente sin CIF verificado.', expression: '', thresholdSummary: 'CIF verificado', approverRole: 'Comercial', evidenceId: '', logic: {objectType: 'Cliente', require: [{attr: 'cif_verificado', op: '==', value: true}], onFail: 'incumplida'}},
    {
      id: 'r2', code: 'R-02', name: 'Crédito alto', description: 'Un límite de crédito superior a 20.000 € lo aprueba Riesgos.', expression: '', thresholdSummary: '> 20.000 €', approverRole: 'Riesgos', evidenceId: '',
      logic: {objectType: 'Cliente', require: [{attr: 'limite_credito', op: '<=', value: 20000}], onFail: 'requiere_aprobacion'},
      action: {title: 'Aprobar el crédito de {objeto}', draft: 'Se aprueba el límite de crédito solicitado para {objeto}.'},
    },
  ],
};
export const casos: TestCase[] = [
  {id: 'CLI-1', title: 'Cliente con todo en regla', objectType: 'Cliente', values: {cif_verificado: true, limite_credito: 5000, contrato_firmado: '2026-10-01'}, relations: []},
  {id: 'CLI-2', title: 'Cliente con crédito alto', objectType: 'Cliente', values: {cif_verificado: true, limite_credito: 50000}, relations: []},
  {id: 'CLI-3', title: 'Cliente sin CIF verificado', objectType: 'Cliente', values: {cif_verificado: false, limite_credito: 1000}, relations: []},
];

const validada = validateDefinition(borrador);
if (!validada.ok) throw new Error(`El producto ya no acepta la definición del reel: ${validada.errors.join('; ')}`);
export const definicion = validada.definition;
export const proceso = assemblePack(seedFromCases(id, casos, definicion), definicion, SAMPLE_NOW);
export const matriz = matrixFrom(proceso, evaluatePack(proceso, {now: SAMPLE_NOW}));
export const hashVersion = policyHash(definicion);

const estado = (obj: string, regla: string) => matriz.find((r) => r.objectId === obj)?.cells.find((c) => c.rule.code === regla)?.estado;
const esperado: [string, string, string][] = [
  ['CLI-1', 'R-01', 'conforme'], ['CLI-1', 'R-02', 'conforme'],
  ['CLI-2', 'R-01', 'conforme'], ['CLI-2', 'R-02', 'requiere_aprobacion'],
  ['CLI-3', 'R-01', 'incumplida'], ['CLI-3', 'R-02', 'conforme'],
];
for (const [o, r, e] of esperado) {
  if (estado(o, r) !== e) throw new Error(`El motor ya no da ${o}/${r} = ${e}, sino ${estado(o, r)}`);
}

export const reglaCredito = definicion.rules.find((r) => r.code === 'R-02')!;
export const logicaCredito = describeLogic(reglaCredito.logic);
const encontrada = proceso.reviewQueue.find((r) => r.ruleCode === 'R-02' && r.targetObjectId === 'CLI-2');
if (!encontrada || encontrada.requiredRole !== 'Riesgos') throw new Error('La acción de R-02 ya no abre una revisión de Riesgos sobre CLI-2');
export const revisionCredito = encontrada;
export const bloqueoComercial = roleBlockReason('Comercial', revisionCredito);
if (!bloqueoComercial) throw new Error('Comercial ya puede aprobar el crédito: el guion deja de ser cierto');

const atributo = (k: string) => definicion.objectTypes[0].attributes.find((a) => a.key === k)!;
const euros = (n: number) => `${String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.')} €`;
export const resumenCaso = (c: TestCase) =>
  Object.entries(c.values)
    .map(([k, v]) => `${atributo(k).label}: ${typeof v === 'boolean' ? (v ? 'sí' : 'no') : typeof v === 'number' ? euros(v) : v}`)
    .join(' · ');
