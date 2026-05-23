import spacy


model_dir="/Users/sartajsyed/Documents/doriot-ai-agents/Market-Research-Agent/app/classifier_model/intent_model"
nlp_inference = spacy.load(model_dir)

# Example test query (feel free to modify).
test_query = "Sequoia Capital i"
doc = nlp_inference(test_query)

print("\nInference results:")
print(f"Query: '{test_query}'")
print("Predicted intent scores:")
for label, score in doc.cats.items():
    print(f"  {label}: {score:.3f}")
