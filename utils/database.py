import os
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, MetaData, Table
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self):
        self.connection_string = os.environ.get('AZURE_SQL_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError("Azure SQL connection string not found in environment variables")
        
        self.engine = create_engine(f"mssql+pyodbc:///?odbc_connect={self.connection_string}")
        self.metadata = MetaData()
        
        # Define tables
        self.classification = Table(
            'classification', self.metadata,
            Column('Material_Code', String(50), primary_key=True),
            Column('Material_Description', String(255)),
            Column('Category', String(50)),
            Column('Region', String(10)),
            Column('Customer_Dedicated', String(5)),
            Column('Proj_Phase', String(50)),
            Column('Base_Type', String(50)),
            Column('Moulding_Type', String(50)),
            Column('Product_Type', String(50)),
            Column('Viscosity', Float),
            Column('pH', Float),
            Column('Fineness', Integer),
            Column('Shelf_Life', Integer),
            Column('Kosher_Certificate', Boolean),
            Column('Country_Claim', String(50))
        )
        
        self.technical_params = Table(
            'technical_parameters', self.metadata,
            Column('Technique', String(50)),
            Column('Segment', String(50)),
            Column('Min_Viscosity', Float),
            Column('Max_Viscosity', Float)
        )
        
        self.nutrition = Table(
            'nutrition', self.metadata,
            Column('Material_Code', String(50), primary_key=True),
            Column('Energy_Value_kCal', Float),
            Column('Energy_Value_kJ', Float),
            Column('Protein_g', Float),
            Column('Total_Carbohydrates_g', Float),
            Column('Sugars_g', Float),
            Column('Total_Fat_g', Float),
            Column('Saturated_Fatty_Acid_g', Float),
            Column('Trans_Fatty_Acid_Tfa_g', Float),
            Column('Fibre_g', Float),
            Column('Sodium_mg', Float),
            Column('Region', String(10))
        )
        
        self.allergens = Table(
            'allergens', self.metadata,
            Column('Material_Code', String(50), primary_key=True),
            Column('Contains_Milk', Boolean),
            Column('Contains_Soya', Boolean),
            Column('Contains_Nuts', Boolean),
            Column('Contains_Gluten', Boolean),
            Column('Suitable_For_Vegans', Boolean),
            Column('Suitable_For_Vegetarians', Boolean)
        )

    def initialize_database(self):
        """Create tables if they don't exist"""
        self.metadata.create_all(self.engine)

    def load_initial_data(self):
        """Load initial data from CSV files to SQL tables"""
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        try:
            # Load classification data
            classification_df = pd.read_csv('reference_data/01_Classification_New.csv')
            classification_df.to_sql('classification', self.engine, if_exists='replace', index=False)
            
            # Load technical parameters
            tech_params_df = pd.read_csv('reference_data/01_Technical_parameters_per_Production_Technique.csv')
            tech_params_df.to_sql('technical_parameters', self.engine, if_exists='replace', index=False)
            
            # Load nutrition data
            nutrition_df = pd.read_csv('reference_data/03_Nutrition.csv')
            nutrition_df.to_sql('nutrition', self.engine, if_exists='replace', index=False)
            
            # Load allergen data
            allergens_df = pd.read_csv('reference_data/04_Allergens.csv')
            allergens_df.to_sql('allergens', self.engine, if_exists='replace', index=False)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_classification_data(self) -> pd.DataFrame:
        """Get classification data from SQL"""
        return pd.read_sql_table('classification', self.engine)

    def get_technical_params_data(self) -> pd.DataFrame:
        """Get technical parameters data from SQL"""
        return pd.read_sql_table('technical_parameters', self.engine)

    def get_nutrition_data(self) -> pd.DataFrame:
        """Get nutrition data from SQL"""
        return pd.read_sql_table('nutrition', self.engine)

    def get_allergens_data(self) -> pd.DataFrame:
        """Get allergens data from SQL"""
        return pd.read_sql_table('allergens', self.engine)
