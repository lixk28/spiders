# Spiders

A collection of web spiders mainly for scraping images to train vision models.

I developed these spiders at my previous job, they might be useful for you :D

If you find some spider is broken, please fire an issue, I will fix it tomorrow.

## Usage

Install dependencies:
```shell
pip install -r requirements.txt
```

How to launch scrapers and customize your scrape tasks:

Check out the top-level code (the `if __name__ == "__main__":` block) in `*/*/scraper.py`s.


## Supported Websites

- [x] Baidu Image: https://image.baidu.com
    - [x] Keyword search
- [x] Mercari: https://www.mercari.com
    - [x] Keyword search
- [x] Vinted: https://www.vinted.com
    - [x] Keyword search
- [x] Free PNG Logos: https://www.freepnglogos.com
    - [x] Keyword search
- [ ] Pinterest
    - [ ] Keyword search
- [ ] Pixiv
    - [ ] Tag search
    - [ ] Illustrator
    - [ ] Personal Collection

## Disclaimer

1. Caution! This is a very **WIP** project! Use it at your own risk!
2. **I'm NOT responsible for any consequences caused by your usage of the code in any approach or format.**

## LICENSE

![WTFPL](http://www.wtfpl.net/wp-content/uploads/2012/12/wtfpl-badge-1.png)
