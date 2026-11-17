from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, render_template, request

bp = Blueprint("calculos", __name__, url_prefix="/calculos")

CENTAVOS = Decimal("0.01")

# (limite superior da base, alíquota, parcela a deduzir) - tabela mensal vigente
FAIXAS_IRPF = [
    (Decimal("2428.80"), Decimal("0"), Decimal("0")),
    (Decimal("2826.65"), Decimal("0.075"), Decimal("182.16")),
    (Decimal("3751.05"), Decimal("0.15"), Decimal("394.16")),
    (Decimal("4664.68"), Decimal("0.225"), Decimal("675.49")),
    (None, Decimal("0.275"), Decimal("908.73")),
]

# regras de 2026 (Lei 15.270/2025)
LIMITE_ISENCAO = Decimal("5000")
LIMITE_REDUTOR = Decimal("7350")
REDUTOR_MAXIMO = Decimal("312.89")
REDUTOR_A = Decimal("978.62")
REDUTOR_B = Decimal("0.133145")


def _arredondar(valor):
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _para_decimal(texto):
    """Converte '5.000,50' ou '5000.50' em Decimal. Levanta ValueError se inválido."""
    texto = (texto or "").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(texto)
    except Exception:
        raise ValueError("Informe um valor numérico válido.")
    if valor < 0:
        raise ValueError("O valor não pode ser negativo.")
    return valor


def brl(valor):
    """Formata Decimal como moeda brasileira: 1234.5 -> R$ 1.234,50."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def calcular_irpf(bruto, deducoes=Decimal("0")):
    """Estima o IRPF mensal. A tabela incide sobre (bruto - deduções);
    o redutor de 2026 é calculado sobre o rendimento bruto."""
    base = max(bruto - deducoes, Decimal("0"))

    aliquota = Decimal("0")
    imposto_tabela = Decimal("0")
    for limite, aliq, deducao in FAIXAS_IRPF:
        if limite is None or base <= limite:
            aliquota = aliq
            imposto_tabela = max(base * aliq - deducao, Decimal("0"))
            break

    if bruto <= LIMITE_ISENCAO:
        redutor = min(REDUTOR_MAXIMO, imposto_tabela)
    elif bruto <= LIMITE_REDUTOR:
        redutor = max(REDUTOR_A - REDUTOR_B * bruto, Decimal("0"))
        redutor = min(redutor, imposto_tabela)
    else:
        redutor = Decimal("0")

    imposto = imposto_tabela - redutor
    return {
        "bruto": brl(_arredondar(bruto)),
        "base": brl(_arredondar(base)),
        "aliquota": f"{aliquota * 100:.1f}".replace(".", ",") + "%",
        "imposto_tabela": brl(_arredondar(imposto_tabela)),
        "redutor": brl(_arredondar(redutor)),
        "imposto": brl(_arredondar(imposto)),
    }


def calcular_decimo_terceiro(salario, meses):
    """13º proporcional: salário / 12 * meses trabalhados."""
    if not 1 <= meses <= 12:
        raise ValueError("Os meses trabalhados devem estar entre 1 e 12.")
    valor = salario / 12 * meses
    return {
        "salario": brl(_arredondar(salario)),
        "meses": meses,
        "valor": brl(_arredondar(valor)),
    }


@bp.route("/painel", methods=("GET", "POST"))
def painel():
    resultado_irpf = None
    resultado_13 = None
    erro_irpf = None
    erro_13 = None

    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "irpf":
            try:
                bruto = _para_decimal(request.form.get("salario_bruto"))
                deducoes = _para_decimal(request.form.get("deducoes") or "0")
                resultado_irpf = calcular_irpf(bruto, deducoes)
            except ValueError as e:
                erro_irpf = str(e)

        elif acao == "decimo":
            try:
                salario = _para_decimal(request.form.get("salario_base"))
                meses = int(request.form.get("meses", ""))
                resultado_13 = calcular_decimo_terceiro(salario, meses)
            except ValueError as e:
                erro_13 = str(e) if "meses" in str(e) or "valor" in str(e) else "Confira os campos."

    return render_template(
        "calculos/index.html",
        resultado_irpf=resultado_irpf,
        resultado_13=resultado_13,
        erro_irpf=erro_irpf,
        erro_13=erro_13,
    )