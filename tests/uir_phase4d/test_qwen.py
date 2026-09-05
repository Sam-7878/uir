from evaluation.uir_phase4d.models.qwen25_backend import Qwen25OllamaBackend

def main():
    b = Qwen25OllamaBackend()
    res = b.generate("Say OK", max_tokens=10)
    print("Qwen result:", res)

if __name__ == "__main__":
    main()
