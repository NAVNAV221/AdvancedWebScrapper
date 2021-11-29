import time
from website import Website

if __name__ == '__main__':
    start_time = time.time()
    page = Website('https://red574890.github.io/colors.github.io/green.html', 'page')
    page_tree = page.crawl_url_by_depth(2)

    print("--- %s seconds ---" % (time.time() - start_time))
