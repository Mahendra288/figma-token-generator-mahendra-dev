CSS_VARIABLE_TEMPLATE = "\t--{}: {};\n"
INDEX_FILE_TEMPLATE = ":root {css_variables}"
TAILWIND_CONFIG_FILE_TEMPLATE = """module.exports = {{
    theme: {{
        colors: {colors},
        spacing: {spacing},
        borderRadius: {border_radius},
        width: {widths},
        textColor:  ({{ theme }}) => theme('colors'),
         padding: ({{ theme }}) => theme('spacing'),
         margin: ({{ theme }}) => ({{
                    auto: 'auto',
                ...theme('spacing'),
            }}),

         backgroundColor: ({{ theme }}) => ({{ ...theme('colors') }}),
         borderColor: ({{ theme }}) => ({{ ...theme('colors') }}),
            }},
         plugins: [{componentPlugins}]

            }}"""
COMPONENTS_PLUGINS_TEMPLATE = """plugin(function ({{ addComponents, theme }}) {{
       addComponents({theme_color_variables})
    }})"""
DIRECTIVES_TEMPLATE = """
@tailwind components;
@tailwind utilities;

@layer components{{
    {components}
}}


@layer utilities{{
    {utilities}
}}
"""
TW_VARIABLE_TEMPLATE = """  .{key} {{
            {value}
        }}\n"""