from lxml import etree
import sys

def process_file(f):
    print('XXX: Processing file: {0}'.format(f))
    basename = f[8:-4]
    print('.{0} {{'.format(basename))

    # open file
    tree = etree.parse(f)
    root = tree.getroot()

    # read attr
    renderer = root.findall('.//renderer-v2')[0]
    if renderer.attrib['type'] == 'categorizedSymbol':
        attr = renderer.attrib['attr']
        process_categorizedSymbol(renderer, attr)
    elif renderer.attrib['type'] == 'singleSymbol':
        process_singleSymbol(root)
    else:
        print('XXX: unknown type')

    print('}')

def process_categorizedSymbol(renderer, attr):
    # attr we look at to determine styles
    # attr -> value: category

    for category in renderer.findall('.//categories//category'):
        symbol_name = category.attrib['symbol']
        value = category.attrib['value']

        query = './/symbols//symbol[@name="{0}"]'.format(symbol_name)
        for symbol in renderer.findall(query):
            print('  [{0}="{1}"] {{'.format(attr, value))
            process_symbol(symbol)
            print('  }')

def process_singleSymbol(renderer):
    symbol = renderer.findall('.//symbol')[0]
    process_symbol(symbol)

def process_symbol(symbol):
    layer = symbol.findall('.//layer')[0]
    if symbol.attrib['type'] == 'fill':
        # color -> polygon-fill
        color = get_prop_color(layer, 'color')
        print('    polygon-fill: {0};'.format(color))

        # color_border -> line-color
        color_border = get_prop_color(layer, 'color_border')
        print('    line-color: {0};'.format(color_border))

        # width_border -> line-width
        width = get_prop(layer, 'width-border')
        if width:
            print('    line-width: {0};'.format(width))

    if symbol.attrib['type'] == 'line':
        # color -> line-color
        color = get_prop_color(layer, 'color')
        print('    line-color: {0};'.format(color))

        # width -> line-width
        width = get_prop(layer, 'width')
        if width:
            print('    line-width: {0};'.format(width))

        # penstyle -> line-dasharray
        penstyle = get_prop_penstyle(layer, 'penstyle')
        if penstyle and penstyle != 'none':
            print('    line-dasharray: {0};'.format(penstyle))

    if symbol.attrib['type'] == 'marker':
        # color -> marker-fill
        color = get_prop_color(layer, 'color')
        print('    marker-fill: {0};'.format(color))

        # color_border -> marker-line-color
        color_border = get_prop_color(layer, 'color_border')
        print('    marker-line-color: {0};'.format(color_border))

        # size -> marker-width
        size = float(get_prop(layer, 'size')) * 5
        print('    marker-width: {0};'.format(size))

def get_prop(layer, prop):
    return find_layer_prop(layer, prop)

def get_prop_color(layer, prop):
    color = find_layer_prop(layer, prop)
    return 'rgba({0})'.format(color)

def get_prop_penstyle(layer, prop):
    penstyle = find_layer_prop(layer, prop)
    if penstyle == 'solid':
        return 'none'
    if penstyle == 'dash':
        return '5, 2'
    if penstyle == 'dot':
        return '1, 1'
    return 'XXX'

def find_layer_prop(layer, prop):
    query = './/prop[@k="{0}"]'.format(prop)
    results = layer.findall(query)
    if not results:
        return None
    return results[0].attrib['v']

def main():
    process_file(sys.argv[1])

if __name__ == '__main__':
    main()
