# frozen_string_literal: true

source "https://rubygems.org"

gem "minimal-mistakes-jekyll"

# Required plugins for Minimal Mistakes
group :jekyll_plugins do
  gem "jekyll-paginate"
  gem "jekyll-sitemap"
  gem "jekyll-gist"
  gem "jekyll-feed"
  gem "jekyll-include-cache"
  gem "jekyll-archives"
  gem "jekyll-remote-theme"
end

gem "html-proofer", "~> 5.0", group: :test

platforms :windows, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

gem "wdm", "~> 0.2.0", :platforms => [:windows]

gem "webrick", "~> 1.8"
