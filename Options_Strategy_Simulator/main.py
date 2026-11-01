import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from finance_functions import black_scholes, calculate_payoff, strategy_metrics

BG = "#0b1220"
PANEL = "#121d2e"
PANEL2 = "#172438"
TEXT = "#e8eef7"
MUTED = "#91a2b8"
GREEN = "#20c997"
RED = "#ff6b6b"
BLUE = "#65a8ff"
GRID = "#2a3a50"

class OptionsSimulator:
    def __init__(self, root):
        self.root = root
        root.title("Options Strategy Simulator | Finance Lab")
        root.geometry("1280x820")
        root.minsize(1100, 720)
        root.configure(bg=BG)
        self.vars = {}
        self._style()
        self._build()
        self.calculate()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2, foreground=TEXT, arrowcolor=TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL2)], foreground=[("readonly", TEXT)])
        style.configure("TEntry", fieldbackground=PANEL2, foreground=TEXT, insertcolor=TEXT, bordercolor=GRID)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=9)

    def _label(self, parent, text, color=MUTED, size=9, bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    def _card(self, parent, title, value, accent=TEXT, subtitle=""):
        frame = tk.Frame(parent, bg=PANEL, highlightbackground=GRID, highlightthickness=1)
        tk.Label(frame, text=title.upper(), bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 3))
        val = tk.Label(frame, text=value, bg=PANEL, fg=accent, font=("Segoe UI", 19, "bold"))
        val.pack(anchor="w", padx=14)
        sub = tk.Label(frame, text=subtitle, bg=PANEL, fg=MUTED, font=("Segoe UI", 8))
        sub.pack(anchor="w", padx=14, pady=(2, 12))
        return frame, val, sub

    def _build(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 12))
        tk.Label(header, text="FINANCE LAB", bg=BG, fg=GREEN, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(header, text="Options Strategy Simulator", bg=BG, fg=TEXT, font=("Segoe UI", 23, "bold")).pack(anchor="w")
        tk.Label(header, text="Model, visualise and compare option payoffs at expiry", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        side = tk.Frame(body, bg=PANEL, width=285, highlightbackground=GRID, highlightthickness=1)
        side.pack(side="left", fill="y", padx=(0, 16))
        side.pack_propagate(False)
        tk.Label(side, text="TRADE CONFIGURATION", bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(16, 12))

        self.strategy = tk.StringVar(value="Buy Call")
        self._label(side, "OPTIONS STRATEGY", color=MUTED, size=8, bold=True).pack(anchor="w", padx=16)
        combo = ttk.Combobox(side, textvariable=self.strategy, values=["Buy Call", "Buy Put", "Bull Call Spread"], state="readonly")
        combo.pack(fill="x", padx=16, pady=(5, 12))
        combo.bind("<<ComboboxSelected>>", lambda e: self._toggle_spread())

        fields = [
            ("Underlying price (₹)", "spot", "2500"),
            ("Strike price (₹)", "strike", "2500"),
            ("Option premium (₹)", "premium", "85"),
            ("Expiry (days)", "days", "30"),
            ("Volatility (%)", "vol", "25"),
            ("Risk-free rate (%)", "rate", "6.5"),
            ("Lot size", "lot", "25"),
            ("Upper strike (spread)", "strike2", "2700"),
            ("Short call premium (spread)", "premium2", "30"),
        ]
        self.field_frames = {}
        for label, key, default in fields:
            f = tk.Frame(side, bg=PANEL)
            f.pack(fill="x", padx=16, pady=4)
            self._label(f, label, size=8, bold=True).pack(anchor="w")
            var = tk.StringVar(value=default)
            self.vars[key] = var
            ent = ttk.Entry(f, textvariable=var)
            ent.pack(fill="x", pady=(3, 0), ipady=3)
            self.field_frames[key] = f

        self._toggle_spread()
        tk.Button(side, text="CALCULATE STRATEGY  →", command=self.calculate, bg=GREEN, fg="#06251e",
                  activebackground="#31ddb0", relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2").pack(fill="x", padx=16, pady=(15, 8), ipady=5)
        tk.Label(side, text="Illustrative model • European options • At-expiry payoff",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 7), wraplength=245, justify="left").pack(anchor="w", padx=16, pady=(3, 12))

        content = tk.Frame(body, bg=BG)
        content.pack(side="left", fill="both", expand=True)
        cards = tk.Frame(content, bg=BG)
        cards.pack(fill="x")
        self.metric_widgets = {}
        for i, (key, title) in enumerate([("breakeven", "Breakeven"), ("maxprofit", "Maximum profit"), ("maxloss", "Maximum loss"), ("bs", "Black–Scholes call")]):
            card, value, sub = self._card(cards, title, "—", BLUE if key == "bs" else TEXT)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0), pady=(0, 12))
            cards.grid_columnconfigure(i, weight=1)
            self.metric_widgets[key] = (value, sub)

        chart_panel = tk.Frame(content, bg=PANEL, highlightbackground=GRID, highlightthickness=1)
        chart_panel.pack(fill="both", expand=True)
        chart_head = tk.Frame(chart_panel, bg=PANEL)
        chart_head.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(chart_head, text="PROFIT / LOSS AT EXPIRY", bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(side="left")
        self.chart_note = tk.Label(chart_head, text="Payoff per lot", bg=PANEL, fg=MUTED, font=("Segoe UI", 8))
        self.chart_note.pack(side="right")
        self.fig = Figure(figsize=(8.8, 4.7), dpi=100, facecolor=PANEL)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=4)

        insight = tk.Frame(content, bg=PANEL, highlightbackground=GRID, highlightthickness=1)
        insight.pack(fill="x", pady=(12, 0))
        tk.Label(insight, text="STRATEGY INSIGHT", bg=PANEL, fg=GREEN, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self.insight_text = tk.Label(insight, text="", bg=PANEL, fg=TEXT, font=("Segoe UI", 9), justify="left", wraplength=850)
        self.insight_text.pack(anchor="w", padx=16, pady=(0, 12))

        footer = tk.Label(self.root, text="FINANCE LAB  •  Educational simulator, not investment advice",
                          bg=BG, fg="#61738c", font=("Segoe UI", 8))
        footer.pack(side="bottom", pady=(0, 8))

    def _toggle_spread(self):
        show = self.strategy.get() == "Bull Call Spread"
        for key in ("strike2", "premium2"):
            self.field_frames[key].pack_forget()
            if show:
                self.field_frames[key].pack(fill="x", padx=16, pady=4)

    def _read(self):
        d = {k: float(v.get()) for k, v in self.vars.items()}
        if d["spot"] <= 0 or d["strike"] <= 0 or d["premium"] < 0 or d["days"] < 0 or d["vol"] < 0 or d["lot"] <= 0:
            raise ValueError("Enter positive prices and lot size; premium, expiry and volatility cannot be negative.")
        if self.strategy.get() == "Bull Call Spread":
            if d["strike2"] <= d["strike"] or d["premium2"] < 0:
                raise ValueError("For a bull call spread, upper strike must exceed lower strike and short premium cannot be negative.")
        return d

    def calculate(self):
        try:
            d = self._read()
            strat = self.strategy.get()
            spot, k, prem, lot = d["spot"], d["strike"], d["premium"], int(d["lot"])
            vol, rate, days = d["vol"] / 100, d["rate"] / 100, d["days"]
            call, put = black_scholes(spot, k, days, vol, rate)

            metrics = strategy_metrics(
                strat, k, prem, lot,
                strike2=d["strike2"],
                premium2=d["premium2"]
            )

            # Expand chart bounds to include a positive breakeven when needed.
            x_min = max(0.0, spot * 0.45)
            x_max = max(spot * 1.65, k * 1.5, d["strike2"] * 1.15)
            be = metrics["breakeven"]
            if be is not None and be > x_max:
                x_max = be * 1.15
            if be is not None and 0 < be < x_min:
                x_min = max(0.0, be * 0.85)

            x = np.linspace(x_min, x_max, 400)
            y = calculate_payoff(
                strat, x, k, prem, d["strike2"], d["premium2"]
            ) * lot

            be_label = metrics["breakeven_label"]
            max_profit = metrics["max_profit_label"]
            max_loss = metrics["max_loss_label"]

            self.metric_widgets["breakeven"][0].config(text=be_label)
            self.metric_widgets["breakeven"][1].config(text="Underlying price at expiry")
            self.metric_widgets["maxprofit"][0].config(text=max_profit)
            self.metric_widgets["maxprofit"][1].config(text="Per lot")
            self.metric_widgets["maxloss"][0].config(text=max_loss)
            self.metric_widgets["maxloss"][1].config(text="Per lot")
            self.metric_widgets["bs"][0].config(text=f"₹{call:,.2f}")
            self.metric_widgets["bs"][1].config(text=f"Theoretical put: ₹{put:,.2f}")

            if strat == "Buy Call":
                explanation = (
                    f"A long call is bullish. It breaks even at ₹{metrics['breakeven']:,.2f}. "
                    f"Maximum loss is the premium paid (₹{metrics['max_loss']:,.2f} per lot); "
                    "upside is theoretically unlimited."
                )
            elif strat == "Buy Put":
                if metrics["breakeven"] is None:
                    be_text = "there is no positive breakeven"
                else:
                    be_text = f"breakeven is ₹{metrics['breakeven']:,.2f}"
                explanation = (
                    f"A long put is bearish; {be_text}. Maximum loss is the premium paid "
                    f"(₹{metrics['max_loss']:,.2f} per lot). Maximum profit occurs if the "
                    "underlying falls to zero."
                )
            else:
                debit = metrics["net_debit"]
                if debit > 0:
                    spread_note = f"The net debit is ₹{debit:,.2f} per share."
                elif debit < 0:
                    spread_note = f"The position opens for a net credit of ₹{abs(debit):,.2f} per share."
                else:
                    spread_note = "The spread has zero net premium."
                explanation = (
                    f"A bull call spread is a bullish, defined-outcome strategy. "
                    f"It buys the ₹{k:,.2f} call and sells the ₹{d['strike2']:,.2f} call. "
                    f"{spread_note} Maximum profit is {max_profit} per lot and maximum loss "
                    f"is {max_loss} per lot."
                )
            self.insight_text.config(text=explanation)

            
            self.ax.clear()
            self.ax.set_facecolor(PANEL)

            # Main payoff curve
            self.ax.plot(
                x, y,
                color=GREEN,
                linewidth=2.8,
                label="Profit / Loss"
            )

            # Zero profit reference
            self.ax.axhline(
                0,
                color="#a9b8ca",
                linewidth=1.2
            )

            # Clear profit and loss zones
            self.ax.fill_between(
                x, y, 0,
                where=(y >= 0),
                color=GREEN,
                alpha=0.20,
                label="Profit zone"
            )

            self.ax.fill_between(
                x, y, 0,
                where=(y < 0),
                color=RED,
                alpha=0.22,
                label="Loss zone"
            )

            # Breakeven annotation
            if be is not None:
                self.ax.axvline(
                    be,
                    color=BLUE,
                    linestyle="--",
                    linewidth=1.8
                )
                self.ax.annotate(
                    f"BREAKEVEN\n₹{be:,.2f}",
                    xy=(be, 0),
                    xytext=(12, 24),
                    textcoords="offset points",
                    color=BLUE,
                    fontsize=9,
                    fontweight="bold",
                    arrowprops=dict(
                        arrowstyle="->",
                        color=BLUE
                    )
                )

            # Current underlying price
            self.ax.axvline(
                spot,
                color="#f6c85f",
                linestyle=":",
                linewidth=1.5,
                label=f"Current spot ₹{spot:,.2f}"
            )

            # Maximum profit reference
            if strat == "Buy Call":
                profit_text = "MAX PROFIT: UNLIMITED"
            else:
                profit_level = metrics["max_profit"]
                self.ax.axhline(
                    profit_level,
                    color=GREEN,
                    linestyle="-.",
                    linewidth=1.4,
                    label=f"Maximum profit ₹{profit_level:,.2f}"
                )
                profit_text = f"MAX PROFIT: ₹{profit_level:,.2f}"

            # Maximum loss reference
            loss_level = -metrics["max_loss"]

            if metrics["max_loss"] > 0:
                self.ax.axhline(
                    loss_level,
                    color=RED,
                    linestyle="-.",
                    linewidth=1.4,
                    label=f"Maximum loss ₹{metrics['max_loss']:,.2f}"
                )

            # Chart title and labels
            self.ax.set_title(
                f"{strat} | Expiry Payoff",
                color=TEXT,
                fontsize=12,
                loc="left",
                pad=15
            )

            self.ax.set_xlabel(
                "Underlying price at expiry (₹)",
                color=MUTED
            )

            self.ax.set_ylabel(
                "Profit / Loss per lot (₹)",
                color=MUTED
            )

            self.ax.tick_params(colors=MUTED, labelsize=9)

            for spine in self.ax.spines.values():
                spine.set_color(GRID)

            self.ax.grid(
                True,
                color=GRID,
                alpha=0.55,
                linewidth=0.7
            )

            self.ax.legend(
                facecolor=PANEL2,
                edgecolor=GRID,
                labelcolor=TEXT,
                fontsize=8,
                loc="best"
            )

            self.fig.tight_layout(pad=2)
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Input error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = OptionsSimulator(root)
    root.mainloop()
