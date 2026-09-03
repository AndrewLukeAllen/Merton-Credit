import sqlalchemy as sq

from sqlalchemy.orm import sessionmaker, declarative_base, relationship

engine = sq.create_engine(
    "sqlite:///merton.db",
    echo = False
)

Base = declarative_base()

class Company(Base):

    __tablename__ = "companies"

    company_id = sq.Column(sq.Integer, primary_key=True, autoincrement= True)

    ticker = sq.Column(sq.String, nullable=False, unique=True)
    sector = sq.Column(sq.String, nullable=False)
    company_name = sq.Column(sq.String, nullable=False)

    market_data = relationship("MarketData", back_populates="company")
    financials = relationship("Financials", back_populates="company")
    merton_results = relationship("MertonResults", back_populates="company")

class MarketData(Base):

    __tablename__ = "market_data"

    # Turns out these are needed to make this work
    __table_args__ = sq.UniqueConstraint("company_id", "date", name="uq_market_company_date"),

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)

    company_id = sq.Column(sq.Integer, sq.ForeignKey("companies.company_id"), nullable=False)

    date = sq.Column(sq.Date)
    close = sq.Column(sq.Float)

    company = relationship("Company", back_populates="market_data")

class Financials(Base):

    __tablename__ = "financials"
    __table_args__ = sq.UniqueConstraint("company_id", "filing_date","period_end", name="uq_financial_company_date"),

    financial_id = sq.Column( sq.Integer,primary_key=True, autoincrement=True)

    company_id = sq.Column(sq.Integer, sq.ForeignKey("companies.company_id"), nullable=False)

    filing_date = sq.Column(sq.Date, nullable=False)
    fiscal_year = sq.Column(sq.Integer,nullable = False)
    fiscal_period = sq.Column(sq.String,nullable = False)
    period_end =sq.Column(sq.Date,nullable=False)

    total_assets = sq.Column(sq.Float)
    total_debt = sq.Column(sq.Float)
    ordinary_shares = sq.Column(sq.Float)

    company = relationship("Company", back_populates="financials")

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

    company = relationship("Company", back_populates="merton_results")


Session = sessionmaker(bind = engine)

session = Session()

def create_tables():
    Base.metadata.create_all(engine)