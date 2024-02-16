import copy
import json

# Load the exported variables from Figma
with open("./raw_figma_tokens.json", "rb") as file:
    input_data = json.load(file)

PRIMITIVES_KEY_NAME = "primitives"
THEME_KEY_NAME = "theme"
LIGHT_THEME_KEY_NAME = "light"
COLORS_KEY_NAME = "Colors"
COMPONENT_COLORS_KEY_NAME = "Component colors"
SPACING_KEY_NAME = "Spacing"
RADIUS_KEY_NAME = "radius"
WIDTH_KEY_NAME = "widths"
CONTAINER_KEY_NAME = "containers"


def generate_clean_style_name(dirty_name):
    return (
        dirty_name.replace(" ", "-")
        .replace(".", "-")
        .replace("(", "")
        .replace(")", "")
        .lower()
    )


def clean_var_name_for_reverence_value(val):
    remove_wrapping_brackets = val[1:-1]
    partially_cleaned_name = "-".join(remove_wrapping_brackets.split(".")[1:])
    clean_reference_value = generate_clean_style_name(partially_cleaned_name)
    return clean_reference_value


def generate_tailwind_var_for_reference_value(val, key):
    clean_reference_value = clean_var_name_for_reverence_value(val)
    return_value = {key: f"<@@$$$<theme('colors.{clean_reference_value}')<@@$$$<"}
    return return_value


# return {{"'{key}': theme({value})".format(key=key, value=clean_reference_value)}}


def generate_tailwind_spacing_var_for_reference_value(val):
    remove_wrapping_brackets = val[1:-1]
    partially_cleaned_name = "-".join(remove_wrapping_brackets.split(" ")[:1])
    partially_cleaned_name = partially_cleaned_name.lower()
    partially_cleaned_name = partially_cleaned_name.replace("spacing", "s")

    clean_reference_value = generate_clean_style_name(partially_cleaned_name)
    return "@apply {clean_reference_value}".format(
        clean_reference_value=clean_reference_value
    )


def generate_css_var_for_reference_value(val):
    clean_reference_value = clean_var_name_for_reverence_value(val)
    return "var(--{clean_reference_value})".format(
        clean_reference_value=clean_reference_value
    )


def generate_index_css_file(data_dict):
    def isReference(val):
        return val.startswith("{")

    colors = data_dict[PRIMITIVES_KEY_NAME][COLORS_KEY_NAME]

    INDEX_FILE_TEMPLATE = ":root {css_variables}"

    base_css_variables = []
    dependent_variables = []
    for cat in sorted(colors.keys()):
        for sub_cat, data in colors[cat].items():
            color = data["$value"]
            key_name = generate_clean_style_name("{}-{}".format(cat, sub_cat))

            CSS_VARIABLE_TEMPLATE = "\t--{}: {};\n"

            if isReference(color):
                dependent_variables.append(
                    CSS_VARIABLE_TEMPLATE.format(
                        key_name, generate_css_var_for_reference_value(color)
                    )
                )
            else:
                base_css_variables.append(CSS_VARIABLE_TEMPLATE.format(key_name, color))

    processed_data = f'{{ \n{"".join(base_css_variables + dependent_variables)}\n }}'
    with open("index.css", "w") as file:
        file.write(INDEX_FILE_TEMPLATE.format(css_variables=processed_data))


def generate_tailwind_config_file(data_dict):
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
    tw_color_variables = {}

    ## Primitive Colors Handling
    colors = data_dict[PRIMITIVES_KEY_NAME][COLORS_KEY_NAME]
    for cat in sorted(colors.keys()):
        for sub_cat in sorted(colors[cat].keys()):
            key_name = generate_clean_style_name("{}-{}".format(cat, sub_cat))
            tw_color_variables[key_name] = "var(--{var_name})".format(var_name=key_name)

    ## Spacing Handling
    primitive_spacing = colors = data_dict[PRIMITIVES_KEY_NAME][SPACING_KEY_NAME]
    tw_spacing_variables = ""
    # for key, value in primitive_spacing.items():
    x = "\n".join(
        [
            "{key}: '{value}px',".format(key=key.split(" ")[0], value=value["$value"])
            for key, value in primitive_spacing.items()
        ]
    )

    spacing = data_dict[SPACING_KEY_NAME.lower()]
    spacing_variables = {}
    for dirty_variable_name in spacing.keys():
        clean_variable_name = generate_clean_style_name(dirty_variable_name)
        dirty_value = spacing[dirty_variable_name]["$value"]
        spacing_variables[clean_variable_name] = (
            generate_tailwind_spacing_var_for_reference_value(dirty_value)
        )

        new_key = dirty_value[1:-1].replace("Spacing.", "")
        x += "'{key}': '{value}px',\n".format(
            key=clean_variable_name.replace("spacing-", ""),
            value=primitive_spacing[new_key]["$value"],
        )

    tw_spacing_variables = f"{{{x}}}"

    ## Radius Handling
    radius_config = colors = data_dict[RADIUS_KEY_NAME]
    tw_radius_variables = {}
    for key, value in radius_config.items():
        tw_radius_variables[key.replace("radius-", "")] = "{}px".format(value["$value"])

    ## Widths Handling
    width_config = colors = data_dict[WIDTH_KEY_NAME]
    tw_width_variables = ""

    for key, value in width_config.items():
        width_template = "'{key}': theme({value}),\n"
        tw_width_variables += width_template.format(
            key=key.replace("width-", ""),
            value="'{}'".format(
                ".".join(value["$value"][1:-1].lower().split()[0].split("."))
            ),
        )
    tw_width_variables = f"{{{tw_width_variables}}}"

    ## component plugins

    # buttons = data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][
    #     COMPONENT_COLORS_KEY_NAME
    # ]["Components"].pop("Buttons")
    # icons = data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][COMPONENT_COLORS_KEY_NAME][
    #     "Components"
    # ].pop("Icons")
    # feat_icons = icons.pop("Featured icons")
    component_plugin_colors = {}
    for _, value in data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][COLORS_KEY_NAME].items():
        component_plugin_colors.update(value)

    components_raw_dict = data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][
        COMPONENT_COLORS_KEY_NAME
    ]["Components"]

    component_plugin_colors.update(components_raw_dict["App store badges"])
    component_plugin_colors.update(components_raw_dict["Application navigation"])
    component_plugin_colors.update(components_raw_dict["Avatars"])
    component_plugin_colors.update(components_raw_dict["Breadcrumbs"])

    for _, value in components_raw_dict["Buttons"].items():
        component_plugin_colors.update(value)

    component_plugin_colors.update(components_raw_dict["Footers"])
    component_plugin_colors.update(components_raw_dict["Header sections"])

    component_plugin_colors.update(components_raw_dict["Icons"].get("Icons", {}))

    for _, value in components_raw_dict["Icons"].get("Featured icons", {}).items():
        component_plugin_colors.update(value)

    component_plugin_colors.update(components_raw_dict["Icons"].get("Social icons", {}))

    component_plugin_colors.update(components_raw_dict["Mockups"])
    component_plugin_colors.update(components_raw_dict["Sliders"])
    component_plugin_colors.update(components_raw_dict["Thumbnail"])
    component_plugin_colors.update(components_raw_dict["Toggles"])
    component_plugin_colors.update(components_raw_dict["Tooltips"])
    component_plugin_colors.update(components_raw_dict["WYSIWYG editor"])

    utilities_raw_dict = data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][
        COMPONENT_COLORS_KEY_NAME
    ]["Utility"]
    for _, value in utilities_raw_dict.items():
        component_plugin_colors.update(value)


    theme_color_variables = {}

    for dirty_variable_name, value in component_plugin_colors.items():
        clean_variable_name = generate_clean_style_name(dirty_variable_name)
        updated_key = ".{}".format(clean_variable_name)

        try:
            dirty_value = value["$value"]
        except Exception as err:
            raise err

        category_name = dirty_variable_name
        if dirty_variable_name == "Text":
            category_name = "color"
        if dirty_variable_name == "Background":
            category_name = "backgroundColor"
        if dirty_variable_name == "Border":
            category_name = "borderColor"

        theme_color_variables[updated_key] = (
            generate_tailwind_var_for_reference_value(dirty_value, category_name)
        )

    keys_to_delete = []
    updated_theme_color_variables = copy.deepcopy(theme_color_variables)
    for key, value in theme_color_variables.items():
        if "-bg" in key or "bg-" in key:
            if "backgroundColor" in value:
                continue
            updated_theme_color_variables[key] = {"backgroundColor": list(value.values())[0]}
        elif "-border" in key or "border-" in key:
            if "backgroundColor" in value:
                continue
            updated_theme_color_variables[key] = {"borderColor": list(value.values())[0]}
        elif (
            ("-fg" in key or "fg-" in key) or ("utility-" in key or "-utility" in key)
        ) and "-text" not in key or "-bg" in key or "-border" in key:
            color_value = list(value.values())[0]
            updated_theme_color_variables[f".text-{key[1:]}"] = {"color": color_value}
            updated_theme_color_variables[f".bg-{key[1:]}"] = {"backgroundColor": color_value}
            updated_theme_color_variables[f".border-{key[1:]}"] = {"borderColor": color_value}
            keys_to_delete.append(key)
        else:
            updated_theme_color_variables[key] = {"color": list(value.values())[0]}

    for key_ in keys_to_delete:
        updated_theme_color_variables.pop(key_)

    COMPONENTS_PLUGINS_TEMPLATE = """plugin(function ({{ addComponents, theme }}) {{
       addComponents({theme_color_variables})
    }})"""

    output_ = TAILWIND_CONFIG_FILE_TEMPLATE.format(
        colors=json.dumps(tw_color_variables, indent=12),
        spacing=str(tw_spacing_variables),
        border_radius=json.dumps(tw_radius_variables, indent=12),
        widths=tw_width_variables,
        componentPlugins=COMPONENTS_PLUGINS_TEMPLATE.format(
            theme_color_variables=json.dumps(updated_theme_color_variables, indent=12)
        ),
    )
    output_ = output_.replace('"<@@$$$<', "")
    output_ = output_.replace('<@@$$$<"', "")
    with open("tailwind.config.js", "w") as file:
        file.write(output_)


def generate_directives_file(data_dict):
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

    # Handling light theme colors
    buttons = data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][
        COMPONENT_COLORS_KEY_NAME
    ]["Components"].pop("Buttons")
    # icons = data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][COMPONENT_COLORS_KEY_NAME][
    #     "Components"
    # ].pop("Icons")
    # feat_icons = icons.pop("Featured icons")
    colors = dict(
        **data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][COLORS_KEY_NAME],
        **{
            "Alpha": data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][
                COMPONENT_COLORS_KEY_NAME
            ]["Alpha"]
        },
        **data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][COMPONENT_COLORS_KEY_NAME][
            "Utility"
        ],
        **data_dict[THEME_KEY_NAME][LIGHT_THEME_KEY_NAME][COMPONENT_COLORS_KEY_NAME][
            "Components"
        ],
        **buttons,
        # **icons,
    )
    theme_color_variables = {}

    # Handling container
    containers = data_dict[CONTAINER_KEY_NAME]
    container_variables = {}
    for dirty_variable_name in containers.keys():
        clean_variable_name = generate_clean_style_name(dirty_variable_name)
        dirty_value = containers[dirty_variable_name]["$value"]
        container_variables[clean_variable_name] = (
            generate_tailwind_spacing_var_for_reference_value(dirty_value)
        )

    # Handling widths
    width = data_dict[WIDTH_KEY_NAME]
    width_variables = {}
    for dirty_variable_name in width.keys():
        clean_variable_name = generate_clean_style_name(dirty_variable_name)
        dirty_value = width[dirty_variable_name]["$value"]
        width_variables[clean_variable_name] = (
            generate_tailwind_spacing_var_for_reference_value(dirty_value)
        )

    # Handling spacings
    spacing = data_dict[SPACING_KEY_NAME.lower()]
    spacing_variables = {}
    for dirty_variable_name in spacing.keys():
        clean_variable_name = generate_clean_style_name(dirty_variable_name)
        dirty_value = spacing[dirty_variable_name]["$value"]
        spacing_variables[clean_variable_name] = (
            generate_tailwind_spacing_var_for_reference_value(dirty_value)
        )

    TW_VARIABLE_TEMPLATE = """  .{key} {{
        {value}
    }}\n"""
    # Compose Components
    components = ""
    for key, value in theme_color_variables.items():
        components += TW_VARIABLE_TEMPLATE.format(key=key, value=value)

    for key, value in container_variables.items():
        components += TW_VARIABLE_TEMPLATE.format(key=key, value=value)

    for key, value in width_variables.items():
        components += TW_VARIABLE_TEMPLATE.format(key=key, value=value)

    for key, value in spacing_variables.items():
        components += TW_VARIABLE_TEMPLATE.format(key=key, value=value)

    output_ = DIRECTIVES_TEMPLATE.format(
        components=components,
        utilities="",
    )
    with open("directives.css", "w") as file:
        file.write(output_)


if __name__ == "__main__":
    generate_index_css_file(input_data)
    generate_tailwind_config_file(input_data)
    generate_directives_file(input_data)

    print("Processing completed successfully. Output written to 'variableOutput.json'.")
