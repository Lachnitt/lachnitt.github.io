source "https://rubygems.org"

# This site is built and deployed by .github/workflows/pages.yml rather than by
# the legacy GitHub Pages builder, so the Jekyll version is ours to choose and
# the `github-pages` gem (which pins Jekyll 3.9.3 and refuses anything it does
# not ship) is no longer needed.
#
# Local preview:
#     bundle install
#     bundle exec jekyll serve --livereload
gem "jekyll", "~> 4.4"
gem "webrick" # dropped from the Ruby stdlib in 3.0; `jekyll serve` needs it

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-gist"
  gem "jekyll-paginate"
  gem "jekyll-redirect-from"
  gem "jekyll-sitemap"
  gem "jemoji"
end
