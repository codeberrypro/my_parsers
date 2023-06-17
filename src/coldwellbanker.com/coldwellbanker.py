import requests
from bs4 import BeautifulSoup

url = "https://www.coldwellbanker.com/city/nj/barnegat/agents"
response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")
agents_block = soup.find("div", {"class": "agents-list"})
agents = agents_block.find_all("div", {"class": "agent-info"})
for agent in agents:
    name = agent.find("h3").text
    phone = agent.find("span", {"class": "phone"}).text
    email = agent.find("a", {"class": "email-link"}).text
    agency = agent.find("h4").text
    print("Name:", name)
    print("Phone:", phone)
    print("Email:", email)
    print("Agency:", agency)
