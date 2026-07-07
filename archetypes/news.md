---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
date: {{ now.Format "2006-01-02" }}
expiry_date: {{ (now.AddDate 0 0 14).Format "2006-01-02" }}
---
