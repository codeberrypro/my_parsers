import requests
from bs4 import BeautifulSoup
import threading


class AgentScraper:
    def __init__(self, url):
        self.url = url
        self.lock = threading.Lock()

    def fetch_agents(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")
        agents_block = soup.find("div", {"class": "agents-list"})
        agents = agents_block.find_all("div", {"class": "agent-info"})
        for agent in agents:
            name = agent.find("h3").text
            phone = agent.find("span", {"class": "phone"}).text
            email = agent.find("a", {"class": "email-link"}).text
            agency = agent.find("h4").text
            with self.lock:
                print("Name:", name)
                print("Phone:", phone)
                print("Email:", email)
                print("Agency:", agency)


if __name__ == '__main__':
    scraper = AgentScraper("https://www.coldwellbanker.com/city/nj/barnegat/agents")
    t1 = threading.Thread(target=scraper.fetch_agents())
    t2 = threading.Thread(target=scraper.fetch_agents())
    t1.start()
    t2.start()
    t1.join()
    t2.join()