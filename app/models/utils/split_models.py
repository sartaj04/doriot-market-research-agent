import re
import os

def split_models(input_file, output_dir):
    with open(input_file, 'r') as f:
        content = f.read()

    # Extract imports
    imports = re.findall(r'from.*import.*\n', content)
    imports = '\n'.join(imports)

    # Extract each model
    model_pattern = r'class (\w+)\(Base\):\n(.*?)(?=class|\Z)'
    models = re.findall(model_pattern, content, re.DOTALL)

    for model_name, model_content in models:
        file_name = f"{model_name.lower()}.py"
        model_file = os.path.join(output_dir, file_name)

        # Add relationships and methods
        enhanced_model = f'''{imports}

class {model_name}(Base):
    __tablename__ = '{model_name.lower()}'
    id = Column(Integer, primary_key=True, index=True)
{model_content}
    # Relationships
{generate_relationships(model_name)}

    # Model methods
{generate_methods(model_name)}
'''
        with open(model_file, 'w') as f:
            f.write(enhanced_model)

def generate_relationships(model_name):
    relationships = {
        'Companies': '''    descriptions = relationship("OrganizationDescriptions", back_populates="company")
    funding_rounds = relationship("FundingRounds", back_populates="company")
    acquisitions_as_acquirer = relationship("Acquisitions", foreign_keys="Acquisitions.acquirer_uuid", back_populates="acquirer")
    acquisitions_as_acquired = relationship("Acquisitions", foreign_keys="Acquisitions.acquiree_uuid", back_populates="acquiree")''',
        
        'FundingRounds': '''    company = relationship("Companies", back_populates="funding_rounds")
    investments = relationship("Investments", back_populates="funding_round")''',
        
        'Investments': '''    funding_round = relationship("FundingRounds", back_populates="investments")
    investor = relationship("Investors", back_populates="investments")''',
        
        # Add more relationships as needed
    }
    return relationships.get(model_name, '    pass  # No relationships defined')

def generate_methods(model_name):
    methods = {
        'Companies': '''    @property
    def total_funding_formatted(self):
        """Return formatted total funding in USD"""
        if self.total_funding_usd:
            return f"${self.total_funding_usd:,.2f}"
        return "No funding data"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "name": self.name,
            "description": self.short_description,
            "total_funding": self.total_funding_formatted,
            "category": self.category_list,
            "founded_on": self.founded_on,
            "location": f"{self.city}, {self.country_code}" if self.city else self.country_code
        }''',
        
        'FundingRounds': '''    @property
    def investment_summary(self):
        """Return funding round summary"""
        return {
            "type": self.investment_type,
            "amount": f"${self.raised_amount_usd:,.2f}" if self.raised_amount_usd else "Undisclosed",
            "date": self.announced_on,
            "investors": len(self.investments) if self.investments else 0
        }''',
        
        # Add more methods as needed
    }
    return methods.get(model_name, '    pass  # No methods defined')

if __name__ == "__main__":
    input_file = "app/models/generated_models.py"
    output_dir = "app/models"
    split_models(input_file, output_dir)