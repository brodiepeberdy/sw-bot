import discord, requests
from bs4 import BeautifulSoup

class MyClient(discord.Client):
    async def on_ready(self):
        print('Now logged on as:', self.user)
    async def on_message(self, message):
        # Won't reply to itself.
        if message.author.id == self.user.id:
            return
        # Explains each command's purpose.
        elif message.content.startswith('?help'):
            await message.reply("**SW Bot's Commands**"
            + "\n" + "`?help`" + " - An overview of what commands this bot uses."
            + "\n" + "`?search [QUERY]`" + " - If you're unsure on the spelling of an article's title, use this command to recieve the top five results for your search query."
            + "\n" + "`?overview [QUERY]`" + " - Provides an overview of the article you've specified. If you're unsure on the spelling of something (which will fail to retrieve the article), try the search function!.")
        # Provides the overview of a queried wiki article.
        elif message.content.startswith('?overview'):
            try:
                # Strips the command, isolating the query / topic specified by the user.
                topic = message.content[10:]
                page = Scraper.scrape_wookieepedia("https://starwars.fandom.com/wiki/", topic)
                overview = Scraper.page_overview(page)
                await message.reply(overview)
            except:
                await message.reply("Looks like I had an issue with your query, please try again. It's likely there is a mispelling, if you're unsure please us the search function! :)")

        elif message.content.startswith('?search'):
            try:
                # Strips the command, isolating the query / topic specified by the user.
                topic = message.content[8:]
                page = Scraper.scrape_wookieepedia("https://starwars.fandom.com/wiki/Special:Search?query=", topic)
                overview = Scraper.search_results(page)
                await message.reply(overview)
            except:
                await message.reply("Looks like I had an issue with your query, please try again. :)")
        elif message.content.startswith('?info'):
            try:
                # Strips the command, isolating the query / topic specified by the user.
                topic = message.content[6:]
                page = Scraper.scrape_wookieepedia("https://starwars.fandom.com/wiki/", topic)
                info = Scraper.page_info(page)
                await message.reply(info)
            except:
                await message.reply("Looks like I had an issue with your query, please try again. :)")



class Scraper():
    # Scrapes and returns a HTML page.
    def scrape_wookieepedia(base, topic):
        url = base + topic
        request = requests.get(url)
        if request.status_code in [200]:
            page = BeautifulSoup(request.text, 'lxml')
            return page

    def page_overview(page):
        overview = page.find('aside', class_="portable-infobox")
        # Removes superscript tags and content from the HTML document.
        [s.extract() for s in overview('sup')]
        # Article Title
        text = "**" + overview.h2.text + "**"
        # The overview part of the article's page.
        sections  = overview.find_all('section')
        for section in sections:
            text = text + "\n" + "***" + section.h2.string + "***" + "\n" + "```"
            divs = section.find_all('div', class_="pi-item pi-data pi-item-spacing pi-border-color")
            for div in divs:
                text = text + "\n" + div.h3.text + ": "
                try:
                    outer_list = div.div.ul.find_all("a")
                    print(outer_list)
                    for outer_item in outer_list:
                        text = text + outer_item.text + ", "
                    text = text[:-2] + "."
                except:
                    text = text + div.div.text + "."

            text = text + "```"
        text = text + "\n" + overview.figure.a.img['src']
        return text[0:4000]
    # First paragraph of an article.
    def page_info(page):
        title = page.find('h1', class_="page-header__title").text
        info = page.find('aside', class_="portable-infobox").find_next('p').text
        text = "**" + title + "**" + "\n" + info
        return text[0:4000]
    # Top five results from a search query.
    def search_results(page):
        results_pane = page.find('div', class_="unified-search__layout__main")
        results  = results_pane.find_all('article')
        text = "**Search Results**" + "\n"
        no_results = 0
        for result in results:
            no_results = no_results + 1
            if no_results > 5:
                break;
            info = result.find('div', class_="unified-search__result__content")
            print(info)
            text = text + "**" + result.h1.text + "**" + "```" + info.text + "```"
        return text[0:4000]

client = MyClient()
client.run('')
