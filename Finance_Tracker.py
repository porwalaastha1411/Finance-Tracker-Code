import tkinter as tk
from tkinter import messagebox, ttk, Toplevel, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import csv
import os
import traceback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DATA_FILE = "transactions.csv"

# ------------------ Data Helpers ------------------

def ensure_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["amount", "category", "note", "date", "type"])  # schema


def load_transactions():
    txs = []
    try:
        with open(DATA_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                txs.append(row)
    except FileNotFoundError:
        return []
    except Exception:
        traceback.print_exc()
    return txs


def write_all_transactions(txs):
    try:
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["amount", "category", "note", "date", "type"])
            for r in txs:
                writer.writerow([
                    r.get("amount", ""),
                    r.get("category", ""),
                    r.get("note", ""),
                    r.get("date", ""),
                    r.get("type", ""),
                ])
        return True
    except Exception as e:
        print("Error writing transactions:", e)
        return False


def append_transaction(tx):
    try:
        with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([tx["amount"], tx["category"], tx["note"], tx["date"], tx["type"]])
        return True
    except Exception as e:
        print("Error appending transaction:", e)
        return False


# Budget functions now operate on transactions.csv as special rows
def get_budget_for_month(month):
    # month like '2025-08'
    txs = load_transactions()
    budget = 0.0
    # pick the latest Budget row for that month (iterate in order, later rows override)
    for r in txs:
        if r.get("type") == "Budget" and r.get("date", "").startswith(month):
            try:
                budget = float(r.get("amount")) if r.get("amount") else 0.0
            except ValueError:
                budget = 0.0
    return budget


def set_budget_for_month(month, limit):
    """
    Store budget as a transaction row:
    amount = limit, category = 'Budget', note = '', date = f'{month}-01', type = 'Budget'
    If a budget row for that month exists, replace it (latest one).
    """
    txs = load_transactions()
    found = False
    # Try to update the last budget row for that month; if none, append new.
    for r in txs:
        if r.get("type") == "Budget" and r.get("date", "").startswith(month):
            r["amount"] = f"{limit:.2f}"
            r["category"] = "Budget"
            r["note"] = ""
            found = True
    if not found:
        txs.append({
            "amount": f"{limit:.2f}",
            "category": "Budget",
            "note": "",
            "date": f"{month}-01",
            "type": "Budget"
        })
    return write_all_transactions(txs)

# ------------------ Calculations ------------------

def calculate_monthly_summary(month):
    txs = load_transactions()
    total_income = 0.0
    total_expense = 0.0
    for r in txs:
        d = r.get("date", "")
        if not d.startswith(month):
            continue
        t = r.get("type", "")
        # skip budget rows when computing income/expense totals
        if t == "Budget":
            continue
        try:
            amt = float(r.get("amount")) if r.get("amount") else 0.0
        except ValueError:
            amt = 0.0
        if t == "Income":
            total_income += amt
        elif t == "Expense":
            total_expense += amt
    budget = get_budget_for_month(month)
    remaining = budget - total_expense
    savings = total_income - total_expense
    return {"income": total_income, "expense": total_expense, "budget": budget, "remaining": remaining, "savings": savings}

# ------------------ GUI ------------------

class FinanceApp:
    def __init__(self, master):
        self.master = master
        master.title("Personal Finance Tracker")
        master.geometry("1000x650")
        master.minsize(800, 550)

        ensure_file()

     
        self.type_var = tk.StringVar(value="Expense")   
        self.amt_var = tk.StringVar()                   
        self.note_var = tk.StringVar()                  
        self.cat_var = tk.StringVar()                   
        self.bud_var = tk.StringVar()                  

      
        top_frame = tk.Frame(master)
        top_frame.pack(fill="x", padx=8, pady=6)

        entry_frame = tk.LabelFrame(top_frame, text="Add Transaction")
        entry_frame.pack(fill="x", side="left", expand=True, padx=6, pady=6)

        tk.Label(entry_frame, text="Amount (₹)").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        tk.Entry(entry_frame, textvariable=self.amt_var, width=20).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        tk.Label(entry_frame, text="Category").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.combo_category = ttk.Combobox(entry_frame, textvariable=self.cat_var, width=30,
                                           values=["Salary", "Food", "Transport", "Electricity Bills", "Telephone/Mobile Bills", "Water Bill", "Entertainment", "Other"])
        self.combo_category.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        tk.Label(entry_frame, text="Note").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        tk.Entry(entry_frame, textvariable=self.note_var, width=40).grid(row=2, column=1, padx=6, pady=6, sticky="w")

        tk.Label(entry_frame, text="Date").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.entry_date = DateEntry(entry_frame, date_pattern='yyyy-mm-dd')
        self.entry_date.set_date(datetime.now())
        self.entry_date.grid(row=0, column=3, padx=6, pady=6)

        tk.Label(entry_frame, text="Type").grid(row=1, column=2, padx=6, pady=6, sticky="e")
        tk.Radiobutton(entry_frame, text="Expense", variable=self.type_var, value="Expense").grid(row=1, column=3, sticky="w")
        tk.Radiobutton(entry_frame, text="Income", variable=self.type_var, value="Income").grid(row=1, column=3, padx=80, sticky="w")

        tk.Button(entry_frame, text="Add Transaction", command=self.add_transaction).grid(row=3, column=0, columnspan=4, pady=8)

        # Budget (uses same transactions.csv)
        budget_frame = tk.LabelFrame(top_frame, text="Budget (stored in transactions.csv)")
        budget_frame.pack(side="right", padx=6, pady=6)
        tk.Label(budget_frame, text="Set budget for current month (₹):").pack(padx=6, pady=6)
        tk.Entry(budget_frame, textvariable=self.bud_var, width=14).pack(padx=6, pady=2)
        tk.Button(budget_frame, text="Set Budget", command=self.set_budget).pack(padx=6, pady=4)
        tk.Button(budget_frame, text="View Summary", command=self.view_summary).pack(padx=6, pady=4)

        # Controls
        controls = tk.Frame(master)
        controls.pack(fill="x", padx=8, pady=4)

        tk.Label(controls, text="Filter Month (YYYY-MM):").pack(side="left", padx=4)
        self.month_filter = tk.Entry(controls, width=10)   # previously filter_month
        self.month_filter.pack(side="left", padx=4)
        self.month_filter.insert(0, datetime.now().strftime("%Y-%m"))

        tk.Label(controls, text="Category:").pack(side="left", padx=4)
        self.cat_filter = ttk.Combobox(controls, values=["", "Salary", "Food", "Transport", "Electricity Bills", "Telephone/Mobile Bills", "Water Bill", "Entertainment", "Other"], width=18)  # previously filter_category
        self.cat_filter.pack(side="left", padx=4)

        tk.Label(controls, text="Type:").pack(side="left", padx=4)
        self.type_filter = ttk.Combobox(controls, values=["", "Expense", "Income"], width=10)  # previously filter_type
        self.type_filter.pack(side="left", padx=4)

        tk.Button(controls, text="Apply Filters", command=self.refresh_history).pack(side="left", padx=6)
        tk.Button(controls, text="Export CSV", command=self.export_filtered).pack(side="left", padx=6)
        tk.Button(controls, text="Pie Charts (Income & Expense)", command=self.plot_both_pies).pack(side="left", padx=6)
        tk.Button(controls, text="Budget vs Spent", command=self.plot_budget_vs_spent).pack(side="left", padx=6)

        # Main area
        main_area = tk.Frame(master)
        main_area.pack(fill="both", expand=True, padx=8, pady=6)

        left = tk.Frame(main_area)
        left.pack(side="left", fill="both", expand=True)

        columns = ("date", "type", "category", "amount", "note")
        self.tree = ttk.Treeview(left, columns=columns, show="headings")
        self.tree.heading('date', text='Date')
        self.tree.heading('type', text='Type')
        self.tree.heading('category', text='Category')
        self.tree.heading('amount', text='Amount')
        self.tree.heading('note', text='Note')

        self.tree.column('date', width=100, anchor='center')
        self.tree.column('type', width=80, anchor='center')
        self.tree.column('category', width=150, anchor='w')
        self.tree.column('amount', width=100, anchor='center')
        self.tree.column('note', width=250, anchor='w')

        vsb = ttk.Scrollbar(left, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        right = tk.LabelFrame(main_area, text='Quick Stats')
        right.pack(side='right', fill='y', padx=6)

        self.lbl_income = tk.Label(right, text='Income: ₹0.00', anchor='w')
        self.lbl_income.pack(fill='x', padx=8, pady=6)
        self.lbl_expense = tk.Label(right, text='Expense: ₹0.00', anchor='w')
        self.lbl_expense.pack(fill='x', padx=8, pady=6)
        self.lbl_budget = tk.Label(right, text='Budget: ₹0.00', anchor='w')
        self.lbl_budget.pack(fill='x', padx=8, pady=6)
        self.lbl_remaining = tk.Label(right, text='Remaining: ₹0.00', anchor='w')
        self.lbl_remaining.pack(fill='x', padx=8, pady=6)
        self.lbl_savings = tk.Label(right, text='Savings: ₹0.00', anchor='w')
        self.lbl_savings.pack(fill='x', padx=8, pady=6)

        tk.Button(right, text='Refresh', command=self.refresh_history).pack(padx=8, pady=8)

        # initial load
        self.refresh_history()

    # ------------------ Actions ------------------

    def add_transaction(self):
        try:
            amt_text = self.amt_var.get().strip()
            if not amt_text:
                raise ValueError('Amount required')
            amt = float(amt_text)
            if amt <= 0:
                raise ValueError('Amount must be positive')
            category = self.cat_var.get().strip() or 'Other'
            note = self.note_var.get().strip()
            date = self.entry_date.get_date().strftime('%Y-%m-%d')
            ttype = self.type_var.get()

            tx = {'amount': f"{amt:.2f}", 'category': category, 'note': note, 'date': date, 'type': ttype}
            ok = append_transaction(tx)
            if not ok:
                messagebox.showerror('Error', 'Failed to save transaction')
                return

            # check budget
            month = date[:7]
            summary = calculate_monthly_summary(month)
            budget = summary['budget']
            if budget > 0 and summary['expense'] > budget:
                messagebox.showwarning('Budget Exceeded', f"You exceeded budget for {month}! Spent: ₹{summary['expense']:.2f} Budget: ₹{budget:.2f}")
            else:
                messagebox.showinfo('Saved', f"{ttype} saved")

            self.clear_entries()
            self.refresh_history()
        except ValueError as e:
            messagebox.showerror('Input Error', str(e))
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Error', 'Unexpected error')

    def clear_entries(self):
        self.amt_var.set('')
        self.note_var.set('')
        self.cat_var.set('')
        self.entry_date.set_date(datetime.now())
        self.type_var.set('Expense')

    def set_budget(self):
        try:
            month = datetime.now().strftime('%Y-%m')
            text = self.bud_var.get().strip()
            if not text:
                raise ValueError('Enter budget')
            limit = float(text)
            if limit < 0:
                raise ValueError('Budget must be >= 0')
            ok = set_budget_for_month(month, limit)
            if ok:
                messagebox.showinfo('Budget', f'Budget ₹{limit:.2f} set for {month}')
                # immediate warning if already exceeded
                summary = calculate_monthly_summary(month)
                if summary['expense'] > limit:
                    messagebox.showwarning('Budget Exceeded', f"Already spent ₹{summary['expense']:.2f} which exceeds the new budget ₹{limit:.2f}")
                self.refresh_history()
            else:
                messagebox.showerror('Error', 'Failed to save budget')
        except ValueError as e:
            messagebox.showerror('Input Error', str(e))

    def view_summary(self):
        month = datetime.now().strftime('%Y-%m')
        s = calculate_monthly_summary(month)
        msg = (
            f"Month: {month}\n"
            f"Income: ₹{s['income']:.2f}\n"
            f"Expense: ₹{s['expense']:.2f}\n"
            f"Budget: ₹{s['budget']:.2f}\n"
            f"Remaining: ₹{s['remaining']:.2f}\n"
            f"Savings: ₹{s['savings']:.2f}"
        )
        if s['remaining'] < 0:
            msg += "\n\n You have exceeded your budget!"
        messagebox.showinfo('Monthly Summary', msg)

    def refresh_history(self):
        # clear tree
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        txs = load_transactions()
        fm = self.month_filter.get().strip()
        fc = self.cat_filter.get().strip()
        ft = self.type_filter.get().strip()

        income_total = 0.0
        expense_total = 0.0

        for r in txs:
            # skip budget rows in normal history view
            if r.get('type') == 'Budget':
                continue
            if fm and not r.get('date','').startswith(fm):
                continue
            if fc and r.get('category','') != fc:
                continue
            if ft and r.get('type','') != ft:
                continue
            self.tree.insert('', 'end', values=(r.get('date',''), r.get('type',''), r.get('category',''), r.get('amount',''), r.get('note','')))
            try:
                if r.get('type') == 'Income':
                    income_total += float(r.get('amount')) if r.get('amount') else 0.0
                elif r.get('type') == 'Expense':
                    expense_total += float(r.get('amount')) if r.get('amount') else 0.0
            except ValueError:
                pass

        # update quick stats for selected month
        month_for_stats = fm or datetime.now().strftime('%Y-%m')
        s = calculate_monthly_summary(month_for_stats)
        self.lbl_income.config(text=f"Income: ₹{s['income']:.2f}")
        self.lbl_expense.config(text=f"Expense: ₹{s['expense']:.2f}")
        self.lbl_budget.config(text=f"Budget: ₹{s['budget']:.2f}")
        self.lbl_remaining.config(text=f"Remaining: ₹{s['remaining']:.2f}")
        self.lbl_savings.config(text=f"Savings: ₹{s['savings']:.2f}")

    def export_filtered(self):
        rows = []
        for iid in self.tree.get_children():
            rows.append(self.tree.item(iid)['values'])
        if not rows:
            messagebox.showinfo('No Data', 'No transactions to export')
            return
        fp = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not fp:
            return
        try:
            with open(fp, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['date','type','category','amount','note'])
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo('Exported', f'Exported {len(rows)} rows to {fp}')
        except Exception:
            traceback.print_exc()
            messagebox.showerror('Error', 'Failed to export')

    def plot_both_pies(self):
        fm = self.month_filter.get().strip() or datetime.now().strftime('%Y-%m')
        txs = load_transactions()
        expense = {}
        income = {}
        for r in txs:
            if not r.get('date','').startswith(fm):
                continue
            t = r.get('type','')
            if t == 'Expense':
                cat = r.get('category') or 'Other'
                try:
                    amt = float(r.get('amount')) if r.get('amount') else 0.0
                except ValueError:
                    amt = 0.0
                expense[cat] = expense.get(cat, 0.0) + amt
            elif t == 'Income':
                cat = r.get('category') or 'Income'
                try:
                    amt = float(r.get('amount')) if r.get('amount') else 0.0
                except ValueError:
                    amt = 0.0
                income[cat] = income.get(cat, 0.0) + amt

        if not expense and not income:
            messagebox.showinfo('No Data', 'No income or expense data for selected month')
            return

        fig, axs = plt.subplots(1, 2, figsize=(12,6))
        if expense:
            axs[0].pie(list(expense.values()), labels=list(expense.keys()), autopct='%1.1f%%', startangle=140)
            axs[0].set_title(f'Expense Distribution ({fm})')
        else:
            axs[0].text(0.5, 0.5, 'No Expense Data', ha='center', va='center')

        if income:
            axs[1].pie(list(income.values()), labels=list(income.keys()), autopct='%1.1f%%', startangle=140)
            axs[1].set_title(f'Income Distribution ({fm})')
        else:
            axs[1].text(0.5, 0.5, 'No Income Data', ha='center', va='center')

        plt.tight_layout()
        self._show_figure(fig, f'Income & Expense Pie Charts - {fm}')

    def plot_budget_vs_spent(self):
        fm = self.month_filter.get().strip() or datetime.now().strftime('%Y-%m')
        s = calculate_monthly_summary(fm)
        labels = ['Budget', 'Spent']
        values = [s['budget'], s['expense']]
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(labels, values)
        ax.set_title(f'Budget vs Spent - {fm}')
        ax.set_ylabel('Amount (₹)')
        self._show_figure(fig, f'Budget vs Spent - {fm}')

    def _show_figure(self, fig, title):
        win = Toplevel(self.master)
        win.title(title)
        # moderate chart window size
        win.geometry('900x500')
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

# ------------------ Run ------------------

def main():
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
