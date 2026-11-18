import pandas as pd
import os

# 交易记录
class TradeRecord:
    def __init__(self, date, session, stock_type, buyer, seller, quantity, price):
        self.date = date
        self.session = session
        self.stock_type = stock_type
        self.buyer = buyer
        self.seller = seller
        self.quantity = quantity
        self.price = price

    def write_to_excel(self, file_name="res/trades.xlsx"):
        if os.path.isfile(file_name):
            existing_df = pd.read_excel(file_name)
        else:
            existing_df = pd.DataFrame(columns=["Trading_Day", "Trading_Session", "Stock_Type", "Buyer_Agent", "Seller_Agent", "Trade_Amount", "Trade_Price"])

        # 将新的交易记录合并到现有DataFrame
        new_records = [[self.date, self.session, self.stock_type, self.buyer, self.seller, self.quantity, self.price]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将所有记录写入到Excel文件
        os.makedirs(os.path.dirname(os.path.abspath(file_name)), exist_ok=True)
        all_records_df.to_excel(file_name, index=False)

def create_trade_record(date, stage, stock, buy_trader, sell_trader, amount, price):
    record = TradeRecord(date, stage, stock, buy_trader, sell_trader, amount, price)
    record.write_to_excel()
    record = None

# 将交易记录列表写入Excel文件（如果文件不存在则创建）

class StockRecord:
    def __init__(self, date, session, stock_a_price, stock_b_price):
        self.date = date
        self.session = session
        self.stock_a_price = stock_a_price
        self.stock_b_price = stock_b_price

    def write_to_excel(self, file_name="res/stocks.xlsx"):
        if os.path.isfile(file_name):
            existing_df = pd.read_excel(file_name)
        else:
            existing_df = pd.DataFrame(columns=["Trading_Day", "Trading_Session", "Stock_A_Price", "Stock_B_Price"])

        # 将新的交易记录合并到现有DataFrame
        new_records = [[self.date, self.session, self.stock_a_price, self.stock_b_price]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将所有记录写入到Excel文件
        os.makedirs(os.path.dirname(os.path.abspath(file_name)), exist_ok=True)
        all_records_df.to_excel(file_name, index=False)

def create_stock_record(date, session, stock_a_price, stock_b_price):
    record = StockRecord(date, session, stock_a_price, stock_b_price)
    record.write_to_excel()
    record = None


class AgentRecordDaily:
    def __init__(self, agent, date, loan_json):
        self.agent = agent
        self.date = date
        self.if_loan = loan_json["loan"]
        self.loan_type = 0
        self.loan_amount = 0
        if self.if_loan == "yes":
            self.loan_type = loan_json["loan_type"]
            self.loan_amount = loan_json["amount"]
        self.will_loan = "no"
        self.will_buy_a = "no"
        self.will_sell_a = "no"
        self.will_buy_b = "no"
        self.will_sell_b = "no"

    def add_estimate(self, js):
        self.will_loan = js["loan"]
        self.will_buy_a = js["buy_A"]
        self.will_sell_a = js["sell_A"]
        self.will_buy_b = js["buy_B"]
        self.will_sell_b = js["sell_B"]

    def write_to_excel(self, file_name="res/agent_day_record.xlsx"):
        if os.path.isfile(file_name):
            existing_df = pd.read_excel(file_name)
        else:
            existing_df = pd.DataFrame(columns=["Agent_ID", "Trading_Day", "Took_Loan", "Loan_Type", "Loan_Amount",
                                                "Predict_Tomorrow_Loan", "Predict_Buy_A", "Predict_Sell_A", "Predict_Buy_B", "Predict_Sell_B"])

        # 将新的交易记录合并到现有DataFrame
        new_records = [[self.agent, self.date, self.if_loan, self.loan_type, self.loan_amount,
                        self.will_loan, self.will_buy_a, self.will_sell_a, self.will_buy_b, self.will_sell_b]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将所有记录写入到Excel文件
        os.makedirs(os.path.dirname(os.path.abspath(file_name)), exist_ok=True)
        all_records_df.to_excel(file_name, index=False)

class AgentRecordSession:
    def __init__(self, agent, date, session, proper, cash, stock_a_value, stock_b_value, action_json):
        self.agent = agent
        self.date = date
        self.session = session
        self.proper = proper
        self.cash = cash
        self.stock_a_value = stock_a_value
        self.stock_b_value = stock_b_value
        self.action_stock = "-"
        self.amount = 0
        self.price = 0
        self.action_type = action_json["action_type"]
        if not self.action_type == "no":
            self.action_stock = action_json["stock"]
            self.amount = action_json["amount"]
            self.price = action_json["price"]

    def write_to_excel(self, file_name="res/agent_session_record.xlsx"):
        if os.path.isfile(file_name):
            existing_df = pd.read_excel(file_name)
        else:
            existing_df = pd.DataFrame(columns=["Agent_ID", "Trading_Day", "Trading_Session", "Total_Assets",
                                                "Cash_Balance", "Stock_A_Value", "Stock_B_Value",
                                                "Order_Type", "Order_Stock", "Order_Amount", "Order_Price"])

        # 将新的交易记录合并到现有DataFrame
        new_records = [[self.agent, self.date, self.session, self.proper, self.cash,
                        self.stock_a_value, self.stock_b_value, self.action_type, self.action_stock,
                        self.amount, self.price]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将所有记录写入到Excel文件
        os.makedirs(os.path.dirname(os.path.abspath(file_name)), exist_ok=True)
        all_records_df.to_excel(file_name, index=False)

def create_agentses_record(agent, date, session, proper, cash, stock_a_value, stock_b_value, action_json):
    record = AgentRecordSession(agent, date, session, proper, cash, stock_a_value, stock_b_value, action_json)
    record.write_to_excel()
    record = None
