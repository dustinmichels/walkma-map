# WalkMA Map

[![Netlify Status](https://api.netlify.com/api/v1/badges/38ed888f-9b23-4999-aa12-499c030a43e2/deploy-status)](https://app.netlify.com/projects/walkma/deploys)

Interactive data visualization of the WalkMA Walk Audit Database.

## Links

[Walk Audit Database](https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/edit?gid=379989993#gid=379989993)

## Overview

### App

The front-end dashboard lives in `app`.

A Netlify function is used to refresh data when the page loads. If this fails, it will fallback on `app/netlify/functions/gsheet/data/last_run.json`. This data can be refreshed by running:

```sh
./refresh_data.sh
```

### Python Code

The `extract/` directory contains a data pipeline. This was for migrating to more robust relational database system and it is currently not in use.
