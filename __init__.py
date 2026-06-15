from otree.api import *
import random


doc = """
Disposition Effect Experiment — Between-subjects trading simulation.
Participants manage a virtual portfolio of 4 stocks over 6 rounds and decide,
each round, whether to sell or hold each stock they still own.
Random assignment to Treatment A or B reverses which stocks start as gains
vs. losses (between-subjects manipulation of reference point).
"""


class C(BaseConstants):
    NAME_IN_URL = 'disposition_experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 6
    SHARES = 10

    STOCKS = ['TECH', 'RETAIL', 'BANK', 'ENERGY']

    STOCK_NAMES = {
        'TECH': 'TechVision Inc.',
        'RETAIL': 'RetailPlus Group',
        'BANK': 'BankCorp SA',
        'ENERGY': 'EnergyFund ETF',
    }
    STOCK_SECTORS = {
        'TECH': 'Technology',
        'RETAIL': 'Consumer',
        'BANK': 'Finance',
        'ENERGY': 'Energy',
    }

    # Price path per stock, one value per round (1-6)
    PRICE_PATHS = {
        'TECH':   [80, 85, 89, 93, 97, 102],
        'RETAIL': [75, 79, 83, 87, 91, 96],
        'BANK':   [70, 66, 62, 58, 54, 50],
        'ENERGY': [65, 61, 57, 52, 48, 44],
    }

    # Purchase ("reference") price per stock, depends on treatment group.
    # Group A: TECH & RETAIL start as GAINS, BANK & ENERGY start as LOSSES.
    # Group B: the reverse (mirror condition).
    BUY_PRICES = {
        'A': {'TECH': 60, 'RETAIL': 58, 'BANK': 82, 'ENERGY': 78},
        'B': {'TECH': 92, 'RETAIL': 88, 'BANK': 55, 'ENERGY': 50},
    }

    LIKERT7 = [(i, str(i)) for i in range(1, 8)]
    LIKERT5 = [(i, str(i)) for i in range(1, 6)]

    DOSPERT_ITEMS = [
        "Investing 10% of your annual income in a moderately growing investment fund.",
        "Investing 5% of your annual income in a very speculative stock or investment.",
        "Borrowing money to invest, knowing you could end up losing more than you put in.",
        "Putting a large portion of your savings into a single investment you believe in strongly.",
        "Continuing to hold an investment that has already lost 30% of its value, hoping it will recover.",
    ]

    GENDER_CHOICES = ['Male', 'Female', 'Non-binary', 'Prefer not to say']
    EXPERIENCE_CHOICES = ['None at all', 'Less than 1 year', '1\u20135 years', 'More than 5 years']
    COUNTRY_CHOICES = [
        'Chile', 'Netherlands', 'Belgium', 'Germany', 'Spain', 'France',
        'Other European country', 'Other',
    ]
    FL1_CHOICES = ['\u20ac102', '\u20ac104', 'More than \u20ac104', 'Less than \u20ac102']
    FL2_CHOICES = ['True', 'False']
    FL3_CHOICES = ['Increases', 'Stays the same', 'Decreases']

    FL1_CORRECT = 'More than \u20ac104'
    FL2_CORRECT = 'True'
    FL3_CORRECT = 'Decreases'


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        for p in subsession.get_players():
            p.participant.vars['treatment'] = random.choice(['A', 'B'])
            p.participant.vars['sold'] = {}
            p.participant.vars['sold_this_round'] = []
    for p in subsession.get_players():
        p.treatment = p.participant.vars['treatment']


class Group(BaseGroup):
    pass


# ────────────────────────────────────────────────────────────────────────────
# Helper functions
# ────────────────────────────────────────────────────────────────────────────

def get_stock_info(player):
    """Return a list of dicts with full info about each of the 4 stocks
    for the CURRENT round, including price, P&L, gain/loss status, and
    whether/when it has been sold."""
    participant = player.participant
    treatment = participant.vars['treatment']
    sold = participant.vars.get('sold', {})
    rn = player.round_number

    stocks = []
    for sid in C.STOCKS:
        buy = C.BUY_PRICES[treatment][sid]
        current = C.PRICE_PATHS[sid][rn - 1]
        pnl_eur = (current - buy) * C.SHARES
        pnl_pct = (current - buy) / buy * 100
        is_sold = sid in sold
        stocks.append(dict(
            id=sid,
            name=C.STOCK_NAMES[sid],
            sector=C.STOCK_SECTORS[sid],
            buy=buy,
            current=current,
            shares=C.SHARES,
            pnl_eur=round(pnl_eur, 0),
            pnl_pct=round(pnl_pct, 1),
            is_gain=current >= buy,
            is_sold=is_sold,
            sold_round=sold.get(sid, {}).get('round') if is_sold else None,
            sold_price=sold.get(sid, {}).get('price') if is_sold else None,
        ))
    return stocks


def active_stock_ids(player):
    sold = player.participant.vars.get('sold', {})
    return [s for s in C.STOCKS if s not in sold]


# ────────────────────────────────────────────────────────────────────────────
# Player model
# ────────────────────────────────────────────────────────────────────────────

class Player(BasePlayer):
    treatment = models.StringField()
    consent = models.BooleanField(
        blank=True,
        widget=widgets.RadioSelect,
        choices=[(True, 'I have read the above and agree to participate')],
        label="",
    )

    # ── Part 1: DOSPERT financial risk attitude (round 1 only) ──
    dospert_1 = models.IntegerField(choices=C.LIKERT7, blank=True, widget=widgets.RadioSelectHorizontal)
    dospert_2 = models.IntegerField(choices=C.LIKERT7, blank=True, widget=widgets.RadioSelectHorizontal)
    dospert_3 = models.IntegerField(choices=C.LIKERT7, blank=True, widget=widgets.RadioSelectHorizontal)
    dospert_4 = models.IntegerField(choices=C.LIKERT7, blank=True, widget=widgets.RadioSelectHorizontal)
    dospert_5 = models.IntegerField(choices=C.LIKERT7, blank=True, widget=widgets.RadioSelectHorizontal)

    # ── Part 2: Trading decisions (one set of fields per round) ──
    decision_TECH = models.StringField(blank=True, choices=[('sell', 'Sell'), ('hold', 'Hold')])
    decision_RETAIL = models.StringField(blank=True, choices=[('sell', 'Sell'), ('hold', 'Hold')])
    decision_BANK = models.StringField(blank=True, choices=[('sell', 'Sell'), ('hold', 'Hold')])
    decision_ENERGY = models.StringField(blank=True, choices=[('sell', 'Sell'), ('hold', 'Hold')])

    # Recorded automatically each round (not user input) — used for PGR/PLR analysis
    isgain_TECH = models.BooleanField(blank=True)
    isgain_RETAIL = models.BooleanField(blank=True)
    isgain_BANK = models.BooleanField(blank=True)
    isgain_ENERGY = models.BooleanField(blank=True)

    pnl_TECH = models.FloatField(blank=True)
    pnl_RETAIL = models.FloatField(blank=True)
    pnl_BANK = models.FloatField(blank=True)
    pnl_ENERGY = models.FloatField(blank=True)

    # ── Regret follow-up (filled only in the round a stock is sold) ──
    regret1_TECH = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="If TechVision Inc.'s price goes up after you sold it, how much regret would you feel?")
    regret2_TECH = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="How much did the thought of future regret influence your decision to sell TechVision Inc.?")

    regret1_RETAIL = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="If RetailPlus Group's price goes up after you sold it, how much regret would you feel?")
    regret2_RETAIL = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="How much did the thought of future regret influence your decision to sell RetailPlus Group?")

    regret1_BANK = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="If BankCorp SA's price goes up after you sold it, how much regret would you feel?")
    regret2_BANK = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="How much did the thought of future regret influence your decision to sell BankCorp SA?")

    regret1_ENERGY = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="If EnergyFund ETF's price goes up after you sold it, how much regret would you feel?")
    regret2_ENERGY = models.IntegerField(
        choices=C.LIKERT5, blank=True, widget=widgets.RadioSelectHorizontal,
        label="How much did the thought of future regret influence your decision to sell EnergyFund ETF?")

    # ── Part 3: Confidence (last round only) ──
    confidence_1 = models.IntegerField(choices=C.LIKERT7, blank=True, widget=widgets.RadioSelectHorizontal)
    confidence_2 = models.IntegerField(choices=C.LIKERT7, blank=True, widget=widgets.RadioSelectHorizontal)

    # ── Demographics (last round only) ──
    age = models.IntegerField(blank=True, min=16, max=110, label="How old are you?")
    gender = models.StringField(blank=True, choices=C.GENDER_CHOICES, widget=widgets.RadioSelect,
                                 label="What is your gender?")
    experience = models.StringField(blank=True, choices=C.EXPERIENCE_CHOICES, widget=widgets.RadioSelect,
                                      label="How much investment experience do you have?")
    country = models.StringField(blank=True, choices=C.COUNTRY_CHOICES,
                                   label="In which country do you currently live?")
    fl1 = models.StringField(blank=True, choices=C.FL1_CHOICES, widget=widgets.RadioSelect,
                              label="If you put \u20ac100 in a savings account with 2% interest per year, "
                                    "how much will you have after 2 years?")
    fl2 = models.StringField(blank=True, choices=C.FL2_CHOICES, widget=widgets.RadioSelect,
                              label="True or false: spreading your money across different investments reduces risk.")
    fl3 = models.StringField(blank=True, choices=C.FL3_CHOICES, widget=widgets.RadioSelect,
                              label="If inflation is 3% and your savings earn 1%, "
                                    "your money's purchasing power over time...")

    # ── Computed summary fields (filled at the end, round NUM_ROUNDS only) ──
    pgr = models.FloatField(blank=True)                 # proportion of gains realized (sold)
    plr = models.FloatField(blank=True)                 # proportion of losses realized (sold)
    disposition_score = models.FloatField(blank=True)   # pgr - plr
    dospert_mean = models.FloatField(blank=True)
    confidence_mean = models.FloatField(blank=True)
    financial_literacy_score = models.IntegerField(blank=True)


# ────────────────────────────────────────────────────────────────────────────
# Pages
# ────────────────────────────────────────────────────────────────────────────

class Consent(Page):
    form_model = 'player'
    form_fields = ['consent']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def error_message(player, values):
        if not values.get('consent'):
            return 'You must agree to participate in order to continue.'


class Dospert(Page):
    form_model = 'player'
    form_fields = ['dospert_1', 'dospert_2', 'dospert_3', 'dospert_4', 'dospert_5']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        return dict(items=list(zip(
            ['dospert_1', 'dospert_2', 'dospert_3', 'dospert_4', 'dospert_5'],
            C.DOSPERT_ITEMS,
        )))


class Instructions(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        return dict(stocks=get_stock_info(player), shares=C.SHARES)


class Trading(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 or len(active_stock_ids(player)) > 0

    @staticmethod
    def get_form_fields(player):
        return [f'decision_{sid}' for sid in active_stock_ids(player)]

    @staticmethod
    def vars_for_template(player):
        stocks = get_stock_info(player)
        active = [s for s in stocks if not s['is_sold']]
        sold = [s for s in stocks if s['is_sold']]
        portfolio_value = sum(s['current'] * C.SHARES for s in active) \
            + sum(s['sold_price'] * C.SHARES for s in sold)
        return dict(
            active_stocks=active,
            sold_stocks=sold,
            round_number=player.round_number,
            num_rounds=C.NUM_ROUNDS,
            portfolio_value=round(portfolio_value),
            progress_pct=round(player.round_number / C.NUM_ROUNDS * 100),
            shares=C.SHARES,
        )

    @staticmethod
    def error_message(player, values):
        for sid in active_stock_ids(player):
            if not values.get(f'decision_{sid}'):
                return 'Please choose Sell or Hold for each stock before continuing.'

    @staticmethod
    def before_next_page(player, timeout_happened):
        participant = player.participant
        sold = participant.vars.get('sold', {})
        sold_this_round = []

        for sid in C.STOCKS:
            current = C.PRICE_PATHS[sid][player.round_number - 1]
            buy = C.BUY_PRICES[participant.vars['treatment']][sid]

            if sid in sold:
                continue

            # record gain/loss status and pnl for this round (for PGR/PLR analysis)
            setattr(player, f'isgain_{sid}', current >= buy)
            setattr(player, f'pnl_{sid}', round((current - buy) * C.SHARES, 2))

            decision = getattr(player, f'decision_{sid}')
            if decision == 'sell':
                sold[sid] = dict(round=player.round_number, price=current)
                sold_this_round.append(sid)

        participant.vars['sold'] = sold
        participant.vars['sold_this_round'] = sold_this_round


class Regret(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return len(player.participant.vars.get('sold_this_round', [])) > 0

    @staticmethod
    def get_form_fields(player):
        fields = []
        for sid in player.participant.vars.get('sold_this_round', []):
            fields += [f'regret1_{sid}', f'regret2_{sid}']
        return fields

    @staticmethod
    def vars_for_template(player):
        sold_ids = player.participant.vars.get('sold_this_round', [])
        sold_stocks = [
            dict(id=sid, name=C.STOCK_NAMES[sid],
                 field1=f'regret1_{sid}', field2=f'regret2_{sid}')
            for sid in sold_ids
        ]
        return dict(
            sold_stocks=sold_stocks,
            sold_names=", ".join(s['name'] for s in sold_stocks),
        )

    @staticmethod
    def error_message(player, values):
        for sid in player.participant.vars.get('sold_this_round', []):
            if not values.get(f'regret1_{sid}') or not values.get(f'regret2_{sid}'):
                return 'Please answer both questions for each stock you sold.'

    @staticmethod
    def before_next_page(player, timeout_happened):
        # Prevent this page from reappearing in later rounds where no
        # Trading page runs (and therefore never resets this list).
        player.participant.vars['sold_this_round'] = []


class Confidence(Page):
    form_model = 'player'
    form_fields = ['confidence_1', 'confidence_2']

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def error_message(player, values):
        if values.get('confidence_1') is None or values.get('confidence_2') is None:
            return 'Please answer both questions before continuing.'


class Demographics(Page):
    form_model = 'player'
    form_fields = ['age', 'gender', 'experience', 'country', 'fl1', 'fl2', 'fl3']

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def error_message(player, values):
        for f in Demographics.form_fields:
            if values.get(f) in [None, '']:
                return 'Please answer all questions before continuing.'

    @staticmethod
    def before_next_page(player, timeout_happened):
        # ── Compute summary measures across all 6 rounds for this participant ──
        all_rounds = player.in_all_rounds()

        gain_total = gain_sold = loss_total = loss_sold = 0
        for p in all_rounds:
            for sid in C.STOCKS:
                decision = p.field_maybe_none(f'decision_{sid}')
                if not decision:
                    continue  # stock wasn't active this round
                is_gain = p.field_maybe_none(f'isgain_{sid}')
                if is_gain:
                    gain_total += 1
                    if decision == 'sell':
                        gain_sold += 1
                else:
                    loss_total += 1
                    if decision == 'sell':
                        loss_sold += 1

        pgr = gain_sold / gain_total if gain_total else 0.0
        plr = loss_sold / loss_total if loss_total else 0.0

        round1 = all_rounds[0]
        dospert_vals = [getattr(round1, f'dospert_{i}') for i in range(1, 6)]
        dospert_mean = sum(dospert_vals) / 5

        c1 = player.field_maybe_none('confidence_1') or 0
        c2 = player.field_maybe_none('confidence_2') or 0
        confidence_mean = (c1 + c2) / 2

        fl_score = 0
        fl_score += player.fl1 == C.FL1_CORRECT
        fl_score += player.fl2 == C.FL2_CORRECT
        fl_score += player.fl3 == C.FL3_CORRECT

        # Write summary fields onto every round's row, so the Data export
        # has the summary available regardless of which round is filtered.
        for p in all_rounds:
            p.pgr = round(pgr, 4)
            p.plr = round(plr, 4)
            p.disposition_score = round(pgr - plr, 4)
            p.dospert_mean = round(dospert_mean, 3)
            p.confidence_mean = round(confidence_mean, 3)
            p.financial_literacy_score = fl_score


class Debrief(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player):
        ds = player.disposition_score
        if ds > 0.1:
            message = "You showed the disposition effect — like most investors!"
        elif ds < -0.1:
            message = "You showed the opposite pattern — selling losers more than winners."
        else:
            message = "You treated gains and losses fairly similarly — no strong bias detected."
        return dict(
            pgr_pct=round(player.pgr * 100),
            plr_pct=round(player.plr * 100),
            message=message,
        )


page_sequence = [
    Consent,
    Dospert,
    Instructions,
    Trading,
    Regret,
    Confidence,
    Demographics,
    Debrief,
]


# ────────────────────────────────────────────────────────────────────────────
# Custom exports
#
# These produce analysis-ready CSVs, available from the oTree admin under
# Sessions > [your session] > Data > "disposition_experiment" custom exports,
# or directly at:
#   /api/export_app_custom?app=disposition_experiment&export_function=custom_export_summary&session_code=XXXX
#   /api/export_app_custom?app=disposition_experiment&export_function=custom_export_decisions&session_code=XXXX
# ────────────────────────────────────────────────────────────────────────────

def custom_export_summary(players):
    """One row per participant (wide format) — ready for SPSS/R.
    Use this for H1, H3, H4, H5, H6 (between-subjects analyses)."""
    yield [
        'participant_code', 'treatment', 'country', 'age', 'gender', 'experience',
        'financial_literacy_score', 'dospert_mean', 'confidence_mean',
        'pgr', 'plr', 'disposition_score',
    ]
    for p in players:
        if p.round_number != C.NUM_ROUNDS:
            continue
        p._is_frozen = False
        yield [
            p.participant.code,
            p.treatment,
            p.field_maybe_none('country'),
            p.field_maybe_none('age'),
            p.field_maybe_none('gender'),
            p.field_maybe_none('experience'),
            p.field_maybe_none('financial_literacy_score'),
            p.field_maybe_none('dospert_mean'),
            p.field_maybe_none('confidence_mean'),
            p.field_maybe_none('pgr'),
            p.field_maybe_none('plr'),
            p.field_maybe_none('disposition_score'),
        ]


def custom_export_decisions(players):
    """One row per participant per stock per round (long format) — ready for
    mixed-effects models, logistic regression (H2, H3), and computing PGR/PLR
    manually if needed."""
    yield [
        'participant_code', 'treatment', 'round', 'stock_id', 'stock_name',
        'decision', 'is_gain', 'pnl_eur', 'regret1', 'regret2',
    ]
    for p in players:
        p._is_frozen = False
        for sid in C.STOCKS:
            decision = p.field_maybe_none(f'decision_{sid}')
            if not decision:
                continue
            yield [
                p.participant.code,
                p.treatment,
                p.round_number,
                sid,
                C.STOCK_NAMES[sid],
                decision,
                int(p.field_maybe_none(f'isgain_{sid}') or 0),
                p.field_maybe_none(f'pnl_{sid}'),
                p.field_maybe_none(f'regret1_{sid}'),
                p.field_maybe_none(f'regret2_{sid}'),
            ]

