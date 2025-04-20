from typing import List
from dataclasses import dataclass
from examples.search_client import SearchClient

@dataclass
class SearchResult:
    title: str
    description: str
    url: str

class MyApplication:
    def __init__(self):
        self.search_client = SearchClient()
    
    def process_search_results(self, query: str) -> List[SearchResult]:
        """
        Führt eine Websuche durch und verarbeitet die Ergebnisse in einem strukturierten Format
        """
        results = []
        response = self.search_client.search(query)
        
        if "error" in response:
            raise Exception(f"Suchfehler: {response['error']['message']}")
            
        # Extrahiere die Textantwort
        content = response["result"]["content"][0]["text"]
        
        # Verarbeite die Ergebnisse
        current_result = {}
        for line in content.split('\n'):
            if line.startswith('Title: '):
                if current_result:
                    results.append(SearchResult(**current_result))
                current_result = {'title': line[7:]}
            elif line.startswith('Description: '):
                current_result['description'] = line[13:]
            elif line.startswith('URL: '):
                current_result['url'] = line[5:]
        
        # Füge das letzte Ergebnis hinzu
        if current_result and len(current_result) == 3:
            results.append(SearchResult(**current_result))
        
        return results
    
    def cleanup(self):
        """
        Beendet den Such-Client sauber
        """
        self.search_client.close()

# Beispiel für die Verwendung
if __name__ == "__main__":
    app = MyApplication()
    
    try:
        # Führe eine Suche durch
        results = app.process_search_results("Python async programming")
        
        # Verarbeite die Ergebnisse
        print("Gefundene Ergebnisse:")
        for result in results:
            print(f"\nTitel: {result.title}")
            print(f"Beschreibung: {result.description}")
            print(f"URL: {result.url}")
            
    finally:
        # Räume auf
        app.cleanup()