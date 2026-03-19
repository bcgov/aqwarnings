--local pandoc = require(pandoc)
--local quarto = require(quarto)

-- Main Accordion Function Shortcode
return {
  ["callout_start"] = function(args, kwargs, meta)
    local title = pandoc.utils.stringify(kwargs["title"])
    local variant = pandoc.utils.stringify(kwargs["variant"])

    if (variant == "") then
      variant = "lightGrey"
    end

    -- todo: aria-labelledby (generate IDs)

    if quarto.doc.is_format("html:js") then
      local markup = "<div class=\"bcds-Callout " .. variant .. "\" role=\"note\">"
      markup = markup .. "<div class=\"bcds-Callout--Container\">"

      if (title ~= nil and title ~= "") then
        markup = markup .. "<div class=\"bcds-Callout--Title\">"
        markup = markup .. title
        markup = markup .. "</div>"
      end

      markup = markup .. "<div class=\"bcds-Callout--Description\">"

      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,

  ["callout_end"] = function(args, kwargs, meta)
    if quarto.doc.is_format("html:js") then
      local markup = "</div></div></div>"
      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,

  ["accordion_controls"] = function(args, kwargs, meta)
    if quarto.doc.is_format("html:js") then
      local markup = ""

      markup = markup .. "<button class='btn accordian-btn' type='button' " ..
          "onclick='BCDSExpandAll()'>" ..
          "Expand All" ..
          "</button>"

      markup = markup .. "<button class='btn accordian-btn' type='button' " ..
          "onclick='BCDSCollapseAll()'>" ..
          "Collapse All" ..
          "</button>"


      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,

  ["accordion_start"] = function(args, kwargs, meta)
    local title = pandoc.utils.stringify(kwargs["title"])
    local headerClass = pandoc.utils.stringify(kwargs["headerClass"])
    local initiallyOpen = pandoc.utils.stringify(kwargs["initiallyOpen"])

    if (title == nil or title == "") then
      title = "Summary"
    end

    if (headerClass == nil) then
      headerClass = ''
    end

    local openAttribute = ''

    if (initiallyOpen == 'true') then
      openAttribute = 'open'
    end

    if quarto.doc.is_format("html:js") then
      local markup = "<details class='bcds-disclosure' " .. openAttribute .. ">"

      markup = markup .. "<summary class='" .. headerClass .. "'>"
      markup = markup .. title
      markup = markup .. "</summary>"

      markup = markup .. "<div class='panel'>"

      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,

  ["accordion_end"] = function(args, kwargs, meta)
    if quarto.doc.is_format("html:js") then
      local markup = "</div></details>"
      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,


  ["card_start"] = function(args, kwargs, meta)
    if quarto.doc.is_format("html:js") then
      local title = pandoc.utils.stringify(kwargs["title"])
      local variant = pandoc.utils.stringify(kwargs["variant"])
      local logo = pandoc.utils.stringify(kwargs["logo"])
      local useIcons = pandoc.utils.stringify(kwargs["useIcons"])
      local width = pandoc.utils.stringify(kwargs["width"])

      local markup = "<div class='bcds-card " .. variant .. " " .. width .. "'>"

      local icon_variant_map = {
        ['success'] = 'check-circle',
        ['info'] = 'info-circle',
        ['warning'] = 'exclamation-triangle',
        ['danger'] = 'exclamation-octagon'
      }

      local selected_icon = nil


      if (logo ~= nil and logo ~= "") then
        markup = markup .. '<img src="' .. logo .. '" class="bcds-card-image" alt="logo"/>'
      end

      if (title ~= nil and title ~= "") then
        markup = markup .. "<h5 class='bcds-card-title'>"
        markup = markup .. title
        markup = markup .. "</h5>"
      end

      if (useIcons == "true") then
        if (variant ~= nil and variant ~= "") then
          selected_icon = icon_variant_map[variant]
          if selected_icon ~= nil then
            markup = markup .. '<i class="card-icon bi bi-' .. selected_icon .. ' ' .. variant .. '"></i>'
          end
        end
      end

      markup = markup .. "<div class='bcds-card-body'>"


      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,

  ["card_end"] = function(args, kwargs, meta)
    if quarto.doc.is_format("html:js") then
      local markup = "</div></div>"
      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,

  ["inline_alert_start"] = function(args, kwargs, meta)
    local title = pandoc.utils.stringify(kwargs["title"])
    local variant = pandoc.utils.stringify(kwargs["variant"])


    if (variant == "") then
      variant = "info"
    end

    local icon_variant_map = {
      ['success'] = 'check-circle',
      ['info'] = 'info-circle',
      ['warning'] = 'exclamation-triangle',
      ['danger'] = 'exclamation-octagon'
    }

    local selected_icon = nil


    if quarto.doc.is_format("html:js") then
      local markup = "<div class='bcds-Inline-Alert " .. variant .. "'>"
      if (variant ~= nil) then
        selected_icon = icon_variant_map[variant]
        if selected_icon ~= nil then
          markup = markup .. '<i class="bcds-Inline-Alert--icon bi bi-' .. selected_icon .. ' ' .. variant .. '"></i>'
        end
      end

      markup = markup .. "<div class='bcds-Inline-Alert--container'>"

      if (title ~= nil) then
        markup = markup .. "<span class='title'>"
        markup = markup .. title
        markup = markup .. "</span>"
      end

      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
  end,

  ["inline_alert_end"] = function(args, kwargs, meta)
    if quarto.doc.is_format("html:js") then
      local markup = "</div></div>"
      return pandoc.RawInline("html", markup)
    else
      return pandoc.Null()
    end
    end,

  ["banner_alert_start"] = function(args, kwargs, meta)
      local title = pandoc.utils.stringify(kwargs["title"])
      local variant = pandoc.utils.stringify(kwargs["variant"])


      if (variant == "") then
        variant = "yellow"
      end

      local icon_variant_map = {
        ['yellow'] = 'exclamation-circle-fill',
        ['orange'] = 'exclamation-diamond-fill',
        ['red'] = 'exclamation-triangle-fill'
      }

      local selected_icon = nil


      if quarto.doc.is_format("html:js") then
        local markup = "<div class='Banner-Alert " .. variant .. "'>"
        if (variant ~= nil) then
          selected_icon = icon_variant_map[variant]
          if selected_icon ~= nil then
            markup = markup .. '<i class="Banner-Alert--icon bi bi-' .. selected_icon .. ' ' .. variant .. '"></i>'
          end
        end

        markup = markup .. "<div class='Banner-Alert--container'>"

        if (title ~= nil) then
          markup = markup .. "<span class='title'>"
          markup = markup .. title
          markup = markup .. "</span>"
        end

        return pandoc.RawInline("html", markup)
      else
        return pandoc.Null()
      end
    end,

    ["banner_alert_end"] = function(args, kwargs, meta)
      if quarto.doc.is_format("html:js") then
        local markup = "</div></div>"
        return pandoc.RawInline("html", markup)
      else
        return pandoc.Null()
      end
    end
}
