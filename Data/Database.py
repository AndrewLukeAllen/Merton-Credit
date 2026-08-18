import sqlalchemy as sq

from sqlalchemy.orm import sessionmaker, declarative_base, relationship

engine = sq.create_engine(
    "sqlite:///merton.db",
    echo = False
)

Base = declarative_base()

class Companies(Base):

    __tablename__ = "companies"

    company_id = sq.Column(sq.Integer, primary_key=True, autoincrement= True)

    ticker = sq.Column(sq.String, nullable=False)
    sector = sq.Column(sq.String, nullable=False)
    company_name = sq.Column(sq.String, nullable=False)

    market_data = sq.relationship("MarketData", back_populates="company")
    financials = sq.relationship("Financials", back_populates="company")
    merton_results = sq.relationship("MertonResults", back_populates="company")

class MarketData(Base):

    __tablename__ = "market_data"

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)

    company_id = sq.Column(sq.Integer, sq.ForeignKey("companies.company_id"), nullable=False)

    date = sq.Column(sq.Date)
    close_price = sq.Column(sq.Float)

    company = sq.relationship("Companies", back_populates="market_data")



class Financials(Base):

    __tablename__ = "financials"

    financial_id = sq.Column( sq.Integer,primary_key=True, autoincrement=True)

    company_id = sq.Column(sq.Integer, sq.ForeignKey("companies.company_id"), nullable=False)
    date = sq.Column(sq.Date, nullable=False)
    total_assets = sq.Column(sq.Float)
    short_term_debt = sq.Column(sq.Float)
    long_term_debt = sq.Column(sq.Float)
    cash = sq.Column(sq.Float)
    ebitda = sq.Column(sq.Float)
    interest_expense = sq.Column(sq.Float)

    company = relationship("Companies", back_populates="financials")

class MertonResults(Base):

    __tablename__ = "merton_results"

    merton_id = sq.Column(sq.Integer,primary_key=True,autoincrement=True)

    company_id = sq.Column(sq.Integer, sq.ForeignKey("companies.company_id"), nullable=False)
    date = sq.Column(sq.Date, nullable=False)
    equity_value = sq.Column(sq.Float)
    equity_volatility = sq.Column(sq.Float)
    default_barrier = sq.Column(sq.Float)
    asset_value = sq.Column(sq.Float)
    asset_volatility = sq.Column(sq.Float)
    distance_to_default = sq.Column(sq.Float)
    probability_of_default = sq.Column(sq.Float)

    company = relationship("Companies", back_populates="merton_results")


Session = sessionmaker(bind = engine)

session = Session()

def create_table():
    Base.metadata.create_all(engine)