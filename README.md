# Diffly

**Game price comparison platform across multiple regions**

Diffly automatically aggregates game prices, allowing users to instantly compare deals and find the cheapest region for any title.
The platform updates game information and regional prices periodically through automated scraping and background tasks. Currently supports Xbox games with plans to expand to other platforms.

The project is live and available here - **[diffly.space](https://diffly.space)**

[![Python](https://img.shields.io/badge/Python-3.13-%233776AB?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-%23092E20?logo=django)](https://www.djangoproject.com/)
[![Scrapy](https://img.shields.io/badge/Scrapy-2.13-%2360A839?logo=scrapy)](https://www.scrapy.org/)
[![Celery](https://img.shields.io/badge/Celery-5.5-%2337814A?logo=celery)](https://docs.celeryq.dev/)

## Features

- **Multi-Region Price Comparison** - Compare game prices across 9+ regions
- **Browsing & Filtering** - Explore all available games, filter by discount status, release year, subscription service, and genre
- **Detailed Game Information** - Descriptions, genres, videos, release info, and more
- **Automated Updates** - Periodic scraping keeps prices and game data fresh
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile

## Tech Stack

### Backend
- **Django**
- **Scrapy**
- **Celery + Celery Beat**
- **Redis**
- **PostgreSQL**
- **Gunicorn (production)**

### Frontend
- **Django Templates**
- **Tailwind CSS**
- **Plyr + HLS.js** for video playback (game trailers)

### Deployment
- **Nginx**
- **Certbot**
- **Ubuntu 22.04 LTS**
- **VPS hosting (self-hosted)**

---

## Author

**Vadym Tantsiura**

- GitHub: [@6SUPER6SONIC6](https://github.com/6SUPER6SONIC6)
- LinkedIn: [Vadym Tantsiura](https://www.linkedin.com/in/vadym-tantsiura-a930a7218/)
- vadym.tantsiura@gmail.com

**Made with ❤️ for gamers who love a good deal**
