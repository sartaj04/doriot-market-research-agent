# scripts/generate_models.py
from dotenv import load_dotenv
import os
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def generate_models():
    engine = create_engine(DB_URL)
    
    # Create MetaData object
    metadata = MetaData()
    metadata.reflect(engine)
    
    # Generate base
    Base = automap_base(metadata=metadata)
    Base.prepare()
    
    # Get all classes
    classes = Base.classes
    
    # Generate model code
    model_code = """from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base

"""
    
    for table_name in metadata.tables:
        table = metadata.tables[table_name]
        class_name = "".join(word.title() for word in table_name.split('_'))
        
        model_code += f"class {class_name}(Base):\n"
        model_code += f"    __tablename__ = '{table_name}'\n\n"
        
        # Add columns
        for column in table.columns:
            col_type = str(column.type)
            model_code += f"    {column.name} = Column({col_type})\n"
        
        model_code += "\n\n"
    
    # Write to file
    os.makedirs('app/models', exist_ok=True)
    with open('app/models/utils/generated_models2.py', 'w') as f:
        f.write(model_code)
    
    print("Models generated successfully")

if __name__ == "__main__":
    generate_models()