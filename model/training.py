import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example
import random
import pandas as pd

# =============================================================================
# 1. Define the Finalized Intents
# =============================================================================

INTENTS = [
    # A. Crunchbase Data–Based Intents
    "COMPANY_PROFILE_QUERY",
    "FUNDING_ROUND_QUERY",
    "ACQUISITION_QUERY",
    "IPO_QUERY",
    "INVESTOR_QUERY",
    "INVESTMENT_DETAILS_QUERY",
    "ORGANIZATION_RELATIONSHIP_QUERY",
    "INVESTMENT_PARTNER_QUERY",
    "FUNDS_QUERY",
    "JOBS_QUERY",
    "PEOPLE_PROFILE_QUERY",
    "EDUCATION_QUERY",
    "COMPETITOR_LOOKUP",
    "LEAD_GENERATION_QUERY",
    "MARKET_ANALYSIS_QUERY",
    # B. News, TechCrunch, and Startup News–Based Intents
    "TECH_NEWS_QUERY",
    "FUNDING_NEWS_QUERY",
    "EVENT_QUERY",
    "MARKET_TRENDS_QUERY",
]

def make_cat_dict(active_intents):
    """
    Returns a dictionary mapping each intent in INTENTS to 1.0 if it is in active_intents,
    otherwise 0.0.
    """
    return {intent: 1.0 if intent in active_intents else 0.0 for intent in INTENTS}

# =============================================================================
# 2. Load Training Data from CSV and Prepare TRAIN_DATA for spaCy
# =============================================================================

# Path to your augmented CSV file.
csv_file = "/Users/sartajsyed/Documents/doriot-ai-agents/Market-Research-Agent/model/systematic_multilabel_training_data.csv"

# Load the CSV into a pandas DataFrame.
df = pd.read_csv(csv_file)

# Convert each row into the format expected by spaCy:
#   (text, {"cats": {<intent>: score, ...}})
TRAIN_DATA = []
for _, row in df.iterrows():
    text = row["query"]
    # Parse the comma-separated labels into a list.
    label_str = row["labels"]
    active_intents = [lbl.strip() for lbl in label_str.split(",") if lbl.strip() != ""]
    cats = make_cat_dict(active_intents)
    TRAIN_DATA.append((text, {"cats": cats}))

print(f"Loaded {len(TRAIN_DATA)} training examples from '{csv_file}'.")

# =============================================================================
# 3. Build the spaCy NLU Model with a Multi-Label Text Categorizer
# =============================================================================

# Create a blank English model.
nlp = spacy.blank("en")

# Use the dedicated multi-label text categorizer.
textcat = nlp.add_pipe("textcat_multilabel")

# Add all defined intent labels to the text categorizer.
for label in INTENTS:
    textcat.add_label(label)

# =============================================================================
# 4. Train the Model
# =============================================================================

n_iter = 20  # Set the number of training iterations.
print("Starting training...")

optimizer = nlp.begin_training()
for i in range(n_iter):
    random.shuffle(TRAIN_DATA)
    losses = {}
    # Use minibatch to generate batches.
    batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
    for batch in batches:
        examples = []
        # Convert each (text, annotation) tuple into an Example object.
        for text, ann in batch:
            doc = nlp.make_doc(text)
            examples.append(Example.from_dict(doc, ann))
        nlp.update(examples, sgd=optimizer, drop=0.2, losses=losses)
    print(f"Iteration {i+1}/{n_iter}, Losses: {losses}")

# =============================================================================
# 5. Save the Trained Model to Disk
# =============================================================================

model_dir = "intent_model"
nlp.to_disk(model_dir)
print(f"Model saved to '{model_dir}'.")

# =============================================================================
# 6. Inference Example
# =============================================================================

# Load the saved model.
nlp_inference = spacy.load(model_dir)

# Example test query (feel free to modify).
test_query = "Show me Apple's profile and its latest funding round."
doc = nlp_inference(test_query)

print("\nInference results:")
print(f"Query: '{test_query}'")
print("Predicted intent scores:")
for label, score in doc.cats.items():
    print(f"  {label}: {score:.3f}")
