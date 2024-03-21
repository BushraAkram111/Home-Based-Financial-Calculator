from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

class FinancialCalculator:
    def __init__(self):
        self.conn = sqlite3.connect("financial_calculator_data.db")
        self.create_table()
        self.frequency_options = ["Monthly", "Yearly"]

    def calculate_expenses(self, data):
        try:
            expenses_data = {}
            for label in data['labels_expenses']:
                category = label
                sub_category = ""
                if "Healthcare" in label:
                    category, sub_category = label.split(" (")
                    sub_category = sub_category[:-1]
                expenses_data.setdefault(category, {})[sub_category] = {
                    "amount": float(data['expenses_entries'][label]),
                    "frequency": data['expenses_entries'][label + "_frequency"]
                }

            total_expenses = sum(
                (expense["amount"] * 12) if expense["frequency"] == "Yearly" else expense["amount"]
                for category in expenses_data.values() for expense in category.values()
            )

            return {"success": True, "total_expenses": total_expenses}

        except ValueError:
            return {"success": False, "message": "Invalid input. Please enter valid numbers."}

    def calculate_budget(self, data):
        try:
            income_data = {label: {
                "amount": float(data['income_entries'][label]),
                "frequency": data['income_entries'][label + "_frequency"]
            } for label in data['labels_income']}

            total_expenses = float(data['total_expenses_entry'])

            total_savings = sum(
                (income["amount"] * 12) if income["frequency"] == "Yearly" else income["amount"]
                for income in income_data.values()
            ) - total_expenses

            return {"success": True, "total_savings": total_savings}

        except ValueError:
            return {"success": False, "message": "Invalid input. Please enter valid numbers."}

    def save_data(self, data):
        try:
            income_data = {label: {
                "amount": float(data['income_entries'][label]),
                "frequency": data['income_entries'][label + "_frequency"]
            } for label in data['labels_income']}

            expenses_data = {}
            for label in data['labels_expenses']:
                category = label
                sub_category = ""
                if "Healthcare" in label:
                    category, sub_category = label.split(" (")
                    sub_category = sub_category[:-1]
                expenses_data.setdefault(category, {})[sub_category] = {
                    "amount": float(data['expenses_entries'][label]),
                    "frequency": data['expenses_entries'][label + "_frequency"]
                }

            total_expenses = sum(
                (expense["amount"] * 12) if expense["frequency"] == "Yearly" else expense["amount"]
                for category in expenses_data.values() for expense in category.values()
            )

            total_savings = sum(
                (income["amount"] * 12) if income["frequency"] == "Yearly" else income["amount"]
                for income in income_data.values()
            ) - total_expenses

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO financial_data (date, total_salary, earned_income_pension, total_expenses, total_savings)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().date(),
                income_data["Total Salary"]["amount"],
                income_data["Earned Income & Pension"]["amount"],
                total_expenses,
                total_savings
            ))

            self.conn.commit()
            cursor.close()

            return {"success": True, "message": "Data saved successfully!", "total_savings": total_savings}

        except ValueError:
            return {"success": False, "message": "Invalid input. Please enter valid numbers."}

    def show_date_dialog(self, data):
        start_date_str = data['start_date']
        end_date_str = data['end_date']

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "message": "Invalid date format. Please use the format: yyyy-mm-dd."}

        result = self.generate_report(start_date, end_date)
        return result

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                total_salary REAL,
                earned_income_pension REAL,
                total_expenses REAL,
                total_savings REAL
            )
        """)
        self.conn.commit()
        cursor.close()

financial_calculator = FinancialCalculator()

@app.route('/')
def home():
    return render_template('financial_calculator.html')

@app.route('/calculate_expenses', methods=['POST'])
def calculate_expenses():
    data = request.json
    result = financial_calculator.calculate_expenses(data)
    return jsonify(result)

@app.route('/calculate_budget', methods=['POST'])
def calculate_budget():
    data = request.json
    result = financial_calculator.calculate_budget(data)
    return jsonify(result)

@app.route('/save_data', methods=['POST'])
def save_data():
    data = request.json
    result = financial_calculator.save_data(data)
    return jsonify(result)

@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.json
    result = financial_calculator.show_date_dialog(data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
