from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

class SummarizationModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = T5Tokenizer.from_pretrained('unicamp-dl/ptt5-base-portuguese-vocab')
        self.model = T5ForConditionalGeneration.from_pretrained('recogna-nlp/ptt5-base-summ').to(self.device)
    
    def summarize(self, text: str) -> str:
        """Summarize the input text using T5 model"""
        # Model and tokenization parameters
        inputs = self.tokenizer.encode(
            text,
            max_length=1024,
            truncation=True,
            return_tensors='pt'
        ).to(self.device)
        
        summary_ids = self.model.generate(
            inputs,
            max_length=512,
            min_length=128,
            num_beams=5,
            no_repeat_ngram_size=3,
            early_stopping=False,
        )
        
        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)