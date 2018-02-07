from __future__ import division, unicode_literals, print_function
import warnings
import os.path
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objs as go
# from plotly.tools import FigureFactory as FF
import plotly.figure_factory as FF
from scipy import stats

__author__ = 'Saurabh Bajaj <sbajaj@lbl.gov>'


# todo: df as attribute, but can still pass x as list or whatever
# todo: sankey
# todo: scatter matrix
# todo: font_scale instead of all options, etc.
# todo: all of them: if mpid or formula in columns, use as interactive index?
# todo: xyplot (X), heatmap (X), histogram, barchart, scatter matrix (X), sankey

class PlotlyFig:
    def __init__(self, df=None, plot_title=None, x_title=None, y_title=None, hovermode='closest', filename='auto',
                 plot_mode='offline', show_offline_plot=True, username=None, api_key=None, textsize=30, ticksize=25,
                 fontfamily=None, height=800, width=1000, scale=None, margins=100, pad=10, marker_scale=1.0, x_type='linear', y_type='linear', hoverinfo='x+y+text'):
        """
        Class for making Plotly plots

        Args:
            df (DataFrame): A pandas dataframe object which can be used to generate several plots.
            plot_title: (str) title of plot
            x_title: (str) title of x-axis
            y_title: (str) title of y-axis
            hovermode: (str) determines the mode of hover interactions. Can be 'x'/'y'/'closest'/False
            filename: (str) name/filepath of plot file
            plot_mode: (str) (i) 'offline': creates and saves plots on the local disk, (ii) 'notebook': to embed plots
                in a IPython/Jupyter notebook, (iii) 'online': save the plot in your online plotly account, or (iv)
                'static': save a static image of the plot locally (but requiring plotly account credentials). Valid
                image formats are 'png', 'svg', 'jpeg', and 'pdf'. The format is taken as the extension of the filename
                or as the supplied format.
                NOTE: Both 'online' and 'static' modes require either the fields 'username' and 'api_key' or
                the plotly credentials file to be set. See plotly website and documentation for details.
            show_offline_plot: (bool) automatically open the plot (the plot is saved either way); only applies to
                'offline' mode
            username: (str) plotly account username
            api_key: (str) plotly account API key
            textsize: (int) size of text of plot title and axis titles
            ticksize: (int) size of ticks
            fontfamily: (str) HTML font family - the typeface that will be applied by the web browser. The web browser
                will only be able to apply a font if it is available on the system which it operates. Provide multiple
                font families, separated by commas, to indicate the preference in which to apply fonts if they aren't
                available on the system. The plotly service (at https://plot.ly or on-premise) generates images on a
                server, where only a select number of fonts are installed and supported. These include "Arial", "Balto",
                 "Courier New", "Droid Sans",, "Droid Serif", "Droid Sans Mono", "Gravitas One", "Old Standard TT",
                 "Open Sans", "Overpass", "PT Sans Narrow", "Raleway", "Times New Roman".
            height: (float) output height (in pixels)
            width: (float) output width (in pixels)
            scale: (float) Increase the resolution of the image by `scale` amount, eg: 3. Only valid for PNG and
                JPEG images.
            margins (float or [float]): Specify the margin (in px) with a list [top, bottom, right, left], or a
                number which will set all margins.
            pad: (float) Sets the amount of padding (in px) between the plotting area and the axis lines
            marker_scale (float): scale the size of all markers w.r.t. defaults
            x_type: (str) Sets the x axis scaling type. Select from 'linear', 'log', 'date', 'category'.
            y_type: (str) Sets the y axis scaling type. Select from 'linear', 'log', 'date', 'category'.
            hoverinfo: (str) Any combination of "x", "y", "z", "text", "name"
                joined with a "+" OR "all" or "none" or "skip".
                Examples: "x", "y", "x+y", "x+y+z", "all"
                Determines which trace information appear on hover. If `none` or `skip` are set, no information is
                displayed upon hovering. But, if `none` is set, click and hover events are still fired.
        Returns: None

        """
        self.df = df
        self.title = plot_title
        self.x_title = x_title
        self.x_type = x_type
        self.y_title = y_title
        self.y_type = y_type
        self.hovermode = hovermode
        self.filename = filename
        self.plot_mode = plot_mode
        self.show_offline_plot = show_offline_plot
        self.username = username
        self.api_key = api_key
        self.textsize = textsize
        self.ticksize = ticksize
        self.fontfamily = fontfamily
        self.height = height
        self.width = width
        self.scale = scale

        if not isinstance(margins, (list, tuple, np.ndarray)):
            margins = [margins] * 4

        self.margins = dict(t=margins[0],
                            b=margins[1] + self.ticksize + self.textsize,
                            r=margins[2],
                            l=margins[3] + self.ticksize + self.textsize,
                            pad=pad)

        # AF: the following is what I added
        self.marker_scale = marker_scale
        self.plot_counter = 1
        self.hoverinfo = hoverinfo

        # Make default layout
        self.layout = dict(
            title=self.title,
            titlefont=dict(size=self.textsize, family=self.fontfamily),
            xaxis=dict(title=self.x_title, type=x_type,
                       titlefont=dict(size=self.textsize, family=self.fontfamily),
                       tickfont=dict(size=self.ticksize, family=self.fontfamily)),
            yaxis=dict(title=self.y_title, type=y_type,
                       titlefont=dict(size=self.textsize, family=self.fontfamily),
                       tickfont=dict(size=self.ticksize, family=self.fontfamily)),
            hovermode=self.hovermode,
            width=self.width,
            height=self.height,
            margin=self.margins
        )

        if self.plot_mode == 'online' or self.plot_mode == 'static':
            if not os.path.isfile('~/.plotly/.credentials'):
                if not self.username:
                    raise ValueError('field "username" must be filled in online plotting mode')
                if not self.api_key:
                    raise ValueError('field "api_key" must be filled in online plotting mode')
                plotly.tools.set_credentials_file(username=self.username, api_key=self.api_key)

        if self.plot_mode == 'static':
            if not self.filename or not self.filename.lower().endswith(
                    ('.png', '.svg', '.jpeg', '.pdf')):
                raise ValueError(
                    'field "filename" must be filled in static plotting mode and must have an extension ending in ('
                    '".png", ".svg", ".jpeg", ".pdf")')

    def _create_plot(self, fig):
        """
        Warning: not to be explicitly called by the user
        Creates the specific plot that has been set up by one of the functions below, and shows and/or saves the plot
        depending on user specification

        Args:
            fig: (dictionary) contains data and layout information

        """
        if self.filename == 'auto':
            filename = 'auto_{}'.format(self.plot_counter)
        else:
            filename = self.filename
        if self.plot_mode == 'offline':
            if not filename.endswith('.html'):
                filename += '.html'
            plotly.offline.plot(fig, filename=filename, auto_open=self.show_offline_plot)

        elif self.plot_mode == 'notebook':
            plotly.offline.init_notebook_mode()  # run at the start of every notebook; version 1.9.4 required
            plotly.offline.iplot(fig)

        elif self.plot_mode == 'online':
            if filename:
                plotly.plotly.plot(fig, filename=filename, sharing='public')
            else:
                plotly.plotly.plot(fig, sharing='public')

        elif self.plot_mode == 'static':
            plotly.plotly.image.save_as(fig, filename=filename,
                    height=self.height, width=self.width, scale=self.scale)
        self.plot_counter += 1


    def xy_plot_simple(self, xy_tuples, markers=None, lines=None,
                       mode='markers', texts=None):
        """
        Make an XY scatter plot, either using arrays of values, or a dataframe.
        Args:
            xy_tuples (tuple or [tuple]): x & y columns of scatter plots
                with possibly different lengths are extracted from this arg
            markers (dict or [dict]): gives the ability to fine tune marker
                of each scatter plot individually if list of dicts passed
            lines (dict or [dict]: similar to markers though only if mode=='lines'
            mode (str): trace style; can be 'markers'/'lines'/'lines+markers'
            texts (list or [list]): to individually set annotation for scatter
                point either the same for all traces or can be set for each
        Returns (XY scatter plot): with one or multiple traces
        """
        if not isinstance(xy_tuples, list):
            xy_tuples = [xy_tuples]
        if not isinstance(texts, list):
            texts = [texts]*len(xy_tuples)
        markers = markers or [{'symbol': 'circle', 'size': 10*self.marker_scale
                    ,'line': {'width': 1}}]*len(xy_tuples)
        lines = lines or [{'dash': 'solid', 'width': 2}]*len(xy_tuples)
        for var in [texts, markers, lines]:
            assert len(var) == len(xy_tuples)
        traces = []
        for i, xy_tup in enumerate(xy_tuples):
            traces.append(go.Scatter(x=xy_tup[0], y=xy_tup[1], mode=mode,
                    marker=markers[i], line=lines[i], text=texts[i], hoverinfo=self.hoverinfo)
                          )

        fig = dict(data=traces, layout=self.layout)
        self._create_plot(fig)


    def xy_plot(self, x_col, y_col, text=None, color='rgba(70, 130, 180, 1)',
                size=6, colorscale='Viridis', legend=None,
                showlegend=False, mode='markers', marker='circle', marker_fill='fill', hoverinfo='x+y+text',
                add_xy_plot=None, marker_outline_width=0, marker_outline_color='black', linedash='solid',
                linewidth=2, lineshape='linear', error_type=None, error_direction=None, error_array=None,
                error_value=None, error_symmetric=True, error_arrayminus=None, error_valueminus=None):
        """
        Make an XY scatter plot, either using arrays of values, or a dataframe.

        Args:
            x_col: (array) x-axis values, which can be a list/array/dataframe column
            y_col: (array) y-axis values, which can be a list/array/dataframe column
            text: (str/array) text to use when hovering over points; a single string, or an array of strings, or a
                dataframe column containing text strings
            color: (str/array) in the format of a (i) color name (eg: "red"), or (ii) a RGB tuple,
                (eg: "rgba(255, 0, 0, 0.8)"), where the last number represents the marker opacity/transparency, which
                must be between 0.0 and 1.0., (iii) hexagonal code (eg: "FFBAD2"), or (iv) name of a dataframe
                numeric column to set the marker color scale to
            size: (int/array) marker size in the format of (i) a constant integer size, or (ii) name of a dataframe
                numeric column to set the marker size scale to. In the latter case, scaled Z-scores are used.
            colorscale: (str) Sets the colorscale. The colorscale must be an array containing arrays mapping a
                normalized value to an rgb, rgba, hex, hsl, hsv, or named color string. At minimum, a mapping for the
                lowest (0) and highest (1) values are required. For example, `[[0, 'rgb(0,0,255)',
                [1, 'rgb(255,0,0)']]`. Alternatively, `colorscale` may be a palette name string of the following list:
                Greys, YlGnBu, Greens, YlOrRd, Bluered, RdBu, Reds, Blues, Picnic, Rainbow, Portland, Jet, Hot,
                Blackbody, Earth, Electric, Viridis
            legend: (str) plot legend
            mode: (str) marker style; can be 'markers'/'lines'/'lines+markers'
            marker: (str) Shape of marker symbol. For all options, please see
                https://plot.ly/python/reference/#scatter-marker-symbol
            marker_fill: (str) Shape fill of marker symbol. Options are "fill"/"open"/"dot"/"open-dot"
            hoverinfo: (str) Any combination of "x", "y", "z", "text", "name" joined with a "+" OR "all" or "none" or
                "skip".
                Examples: "x", "y", "x+y", "x+y+z", "all"
                default: "x+y+text"
                Determines which trace information appear on hover. If `none` or `skip` are set, no information is
                displayed upon hovering. But, if `none` is set, click and hover events are still fired.
            showlegend: (bool) show legend or not
            add_xy_plot: (list) of dictionaries, each of which contain additional data to add to the xy plot. Keys are
                names of arguments to the original xy_plot method - required keys are 'x_col', 'y_col', 'text', 'mode',
                'name', 'color', 'size'. Values are corresponding argument values in the same format as for the
                original xy_plot. Use None for values not to be set, else a KeyError will be raised. Optional keys are
                'marker' and 'marker_fill' (same format as root keys)
            marker_outline_width: (int) thickness of marker outline
            marker_outline_color: (str/array) color of marker outline - accepts similar formats as other color variables
            linedash: (str) sets the dash style of a line. Options are 'solid'/'dash'
            linewidth: (int) sets the line width (in px)
            lineshape: (str) determines the line shape. With "spline" the lines are drawn using spline interpolation
            error_type: (str) Determines the rule used to generate the error bars. Options are,
                (i) "data": bar lengths are set in variable `error_array`/'error_arrayminus',
                (ii) "percent": bar lengths correspond to a percentage of underlying data. Set this percentage in the
                   variable 'error_value'/'error_valueminus',
                (iii) "constant": bar lengths are of a constant value. Set this constant in the variable
                'error_value'/'error_valueminus'
            error_direction: (str) direction of error bar, "x"/"y"
            error_array: (list/array/series) Sets the data corresponding the length of each error bar.
                Values are plotted relative to the underlying data
            error_value: (float) Sets the value of either the percentage (if `error_type` is set to "percent") or
                the constant (if `error_type` is set to "constant") corresponding to the lengths of the error bars.
            error_symmetric: (bool) Determines whether or not the error bars have the same length in both direction
                (top/bottom for vertical bars, left/right for horizontal bars
            error_arrayminus: (list/array/series) Sets the data corresponding the length of each error bar in the bottom
                (left) direction for vertical (horizontal) bars Values are plotted relative to the underlying data.
            error_valueminus: (float) Sets the value of either the percentage (if `error_type` is set to "percent") or
                the constant (if `error_type` is set to "constant") corresponding to the lengths of the error bars in
                the bottom (left) direction for vertical (horizontal) bars
        Returns: XY scatter plot

        """
        if isinstance(color, str):
            showscale = False
        else:
            showscale = True

        # Use z-scores for sizes
        # If size is a list, convert to array for z-score calculation
        if isinstance(size, list):
            size = np.array(size)
        if isinstance(size, pd.Series):
            size = (stats.zscore(size) + 5) * 3

        if marker_fill != 'fill':
            if marker_fill == 'open':
                marker_fill += '-open'
            elif marker_fill == 'dot':
                marker_fill += '-dot'
            elif marker_fill == 'open-dot':
                marker_fill += '-open-dot'
            else:
                raise ValueError('Invalid marker fill')

        trace0 = go.Scatter(
            x=x_col,
            y=y_col,
            text=text,
            mode=mode,
            name=legend,
            hoverinfo=hoverinfo,
            marker=dict(
                size=size,
                color=color,
                colorscale=colorscale,
                showscale=showscale,
                line=dict(width=marker_outline_width, color=marker_outline_color,
                          colorscale=colorscale),
                symbol=marker,
                colorbar=dict(tickfont=dict(size=int(0.75 * self.ticksize), family=self.fontfamily))
            ),
            line=dict(dash=linedash, width=linewidth, shape=lineshape)
        )

        # Add error bars
        if error_type:
            if error_direction is None:
                raise ValueError(
                    "The field 'error_direction' must be populated if 'err_type' is specified")
            if error_type == 'data':
                if error_symmetric:
                    trace0['error_' + error_direction] = dict(type=error_type, array=error_array)
                else:
                    if not error_arrayminus:
                        raise ValueError(
                            "Please specify error bar lengths in the negative direction")
                    trace0['error_' + error_direction] = dict(type=error_type, array=error_array,
                                                              arrayminus=error_arrayminus)
            elif error_type == 'constant' or error_type == 'percent':
                if error_symmetric:
                    trace0['error_' + error_direction] = dict(type=error_type, value=error_value)
                else:
                    if not error_valueminus:
                        raise ValueError(
                            "Please specify error bar lengths in the negative direction")
                    trace0['error_' + error_direction] = dict(type=error_type, value=error_value,
                                                              valueminus=error_valueminus)
            else:
                raise ValueError(
                    "Invalid error bar type. Please choose from 'data'/'constant'/'percent'.")

        data = [trace0]

        # Additional XY plots
        if add_xy_plot:
            for plot_data in add_xy_plot:

                # Check for symbol parameters, if not present, assign defaults
                if 'marker' not in plot_data:
                    plot_data['marker'] = 'circle'
                    if 'marker_fill' in plot_data:
                        plot_data['marker'] += plot_data['marker_fill']

                data.append(
                    go.Scatter(
                        x=plot_data['x_col'],
                        y=plot_data['y_col'],
                        text=plot_data['text'],
                        mode=plot_data['mode'],
                        name=plot_data['legend'],
                        hoverinfo=hoverinfo,
                        marker=dict(
                            color=plot_data['color'],
                            size=plot_data['size'],
                            colorscale=colorscale,  # colorscale is fixed to that of the main plot
                            showscale=showscale,  # showscale is fixed to that of the main plot
                            line=dict(width=marker_outline_width, color=marker_outline_color,
                                      colorscale=colorscale),
                            symbol=plot_data['marker'],
                            colorbar=dict(tickfont=dict(size=int(0.75 * self.ticksize),
                                                        family=self.fontfamily))
                        )
                    )
                )

        # Add legend
        self.layout['showlegend'] = showlegend

        fig = dict(data=data, layout=self.layout)

        self._create_plot(fig)



    def heatmap_plot(self, data, x_labels=None, y_labels=None, colorscale='Viridis', colorscale_range=None,
                     annotations_text=None, annotations_text_size=20, annotations_color='white'):
        """
        Make a heatmap plot, either using 2D arrays of values, or a dataframe.

        Args:
            data: (array) an array of arrays. For example, in case of a pandas dataframe 'df', data=df.values.tolist()
            x_labels: (array) an array of strings to label the heatmap columns
            y_labels: (array) an array of strings to label the heatmap rows
            colorscale: (str/array) Sets the colorscale. The colorscale must be an array containing arrays mapping a
                normalized value to an rgb, rgba, hex, hsl, hsv, or named color string. At minimum, a mapping for the
                lowest (0) and highest (1) values are required. For example, `[[0, 'rgb(0,0,255)',
                [1, 'rgb(255,0,0)']]`. Alternatively, `colorscale` may be a palette name string of the following list:
                Greys, YlGnBu, Greens, YlOrRd, Bluered, RdBu, Reds, Blues, Picnic, Rainbow, Portland, Jet, Hot,
                Blackbody, Earth, Electric, Viridis
            colorscale_range: (array) Sets the minimum (first array item) and maximum value (second array item)
                of the colorscale
            annotations_text: (array) an array of arrays, with each value being a string annotation to the corresponding
                value in 'data'
            annotations_text_size: (int) size of annotation text
            annotations_color: (str/array) color of annotation text - accepts similar formats as other color variables

        Returns: heatmap plot

        """
        if not colorscale_range:
            colorscale_min = None
            colorscale_max = None
        elif len(colorscale_range) == 2:
            colorscale_min = colorscale_range[0]
            colorscale_max = colorscale_range[1]
        else:
            raise ValueError("The field 'colorscale_range' must be a list with two values.")

        if annotations_text:
            annotations = []

            for n, row in enumerate(data):
                for m, val in enumerate(row):
                    var = annotations_text[n][m]
                    annotations.append(
                        dict(
                            text=str(var),
                            x=x_labels[m], y=y_labels[n],
                            xref='x1', yref='y1',
                            font=dict(color=annotations_color, size=annotations_text_size,
                                      family=self.fontfamily),
                            showarrow=False)
                    )
        else:
            annotations = []

        trace0 = go.Heatmap(
            z=data,
            colorscale=colorscale,
            x=x_labels,
            y=y_labels,
            zmin=colorscale_min, zmax=colorscale_max,
            colorbar=dict(tickfont=dict(size=int(0.75 * self.ticksize), family=self.fontfamily))
        )

        data = [trace0]

        # Add annotations
        self.layout['annotations'] = annotations

        fig = dict(data=data, layout=self.layout)

        self._create_plot(fig)

    def violin_plot(self, data=None, cols=None, group_col=None, groups=None, title=None, colors=None, use_colorscale=False):
        """
        Create a violin plot using Plotly.

        Args:
            data: (DataFrame or list) A dataframe containing at least one numerical column. Also accepts lists of numerical values. If None, uses the dataframe passed into the constructor.
            cols: ([str]) The labels for the columns of the dataframe to be included in the plot. Not used if data is passed in as list.
            group_col: (str) Name of the column containing the group for each row, if it exists. Used only if there is one entry in cols.
            groups: ([str]): All group names to be included in the violin plot. Used only if there is one entry in cols.
            title: (str) Title of the violin plot
            colors: (str/tuple/list/dict) either a plotly scale name (Greys, YlGnBu, Greens, YlOrRd, Bluered, RdBu,
                Reds, Blues, Picnic, Rainbow, Portland, Jet, Hot, Blackbody, Earth, Electric, Viridis), an rgb or hex
                color, a color tuple, a list of colors or a dictionary. An rgb color is of the form 'rgb(x, y, z)'
                where x, y and z belong to the interval [0, 255] and a color tuple is a tuple of the form (a, b, c)
                where a, b and c belong to [0, 1]. If colors is a list, it must contain valid color types as its
                members. If colors is a dictionary, its keys must represent group names, and corresponding values must
                be valid color types (str).
            use_colorscale: (bool) Only applicable if grouping by another variable. Will implement a colorscale based
                on the first 2 colors of param colors. This means colors must be a list with at least 2 colors in it
                (Plotly colorscales are accepted since they map to a list of two rgb colors)


        Returns: a Plotly violin plot

        """
        if data is None:
            if cols is None or self.df is None:
                raise ValueError("Violin plot requires either dataframe labels and a dataframe or a list of numerical values.")
            data = self.df

        if isinstance(data, pd.DataFrame):
            if groups is None:
                if group_col is None:
                    grouped = pd.DataFrame({'data': [], 'group': []})

                    for col in cols:
                        d = data[col].tolist()
                        temp_df = pd.DataFrame({'data': d, 'group': [col] * len(d)})
                        grouped = grouped.append(temp_df)
                    data = grouped
                    group_col = 'group'
                    groups = cols
                    cols = ['data']
                else:
                    groups = data[group_col].unique()
            else:
                if group_col is None:
                    raise ValueError("Please specify group_col, the label of the column containing the groups for each row.")

            use_colorscale = True
            group_stats = {}

            for g in groups:
                group_data = data.loc[data[group_col] == g]
                group_stats[g] = np.median(group_data[cols])

            # Filter out groups from dataframe that have only 1 row.
            group_value_counts = data[group_col].value_counts().to_dict()

            for j in group_value_counts:
                if group_value_counts[j] == 1:
                    data = data[data[group_col] != j]
                    warnings.warn('Omitting rows with group = {} which have only one row in the dataframe.'.format(j))
        else:
            if isinstance(data, pd.Series):
                data = data.tolist()

            data = pd.DataFrame({'data': np.asarray(data)})
            cols = ['data']
            group_col = None
            group_stats = None

        fig = FF.create_violin(data=data, data_header=cols[0], group_header=group_col, title=title,
                               height=self.height, width=self.width, colors=colors, use_colorscale=use_colorscale,
                               group_stats=group_stats)

        # Cannot add x-axis title as the above object populates it with group names.
        fig.update(dict(
            layout=dict(
                title=self.title,
                titlefont=dict(size=self.textsize, family=self.fontfamily),
                yaxis=dict(title=self.y_title, type=self.y_type,
                           titlefont=dict(size=self.textsize, family=self.fontfamily),
                           tickfont=dict(size=self.ticksize, family=self.fontfamily)),
            )
        ))

        # Change sizes in all x-axis
        for item in fig['layout']:
            if item.startswith('xaxis'):
                fig['layout'][item].update(
                    dict(
                        titlefont=dict(size=self.textsize, family=self.fontfamily),
                        tickfont=dict(size=self.ticksize, family=self.fontfamily)
                    )
                )
        self._create_plot(fig)

    def scatter_matrix(self, df, colbar_col=None, marker=None, text=None,
                       height=800, width=1000, **kwargs):
        """
        Create a Plotly scatter matrix plot from dataframes using Plotly.
        Args:
            df (pandas.DataFrame): scatter matrix plotted for all columns
            colbar_col: (str) name of the column used for colorbar
            marker (dict): if size is set, it will override the automatic size
            text (see PlotlyFig.xy_plot documentation):
            height (int/float): sets the height of the chart
            width (int/float): sets the width of the chart
            **kwargs: keyword arguments of scatterplot. Forbidden args are
                'size', 'color' and 'colorscale' in 'marker'. See example below
        Returns: a Plotly scatter matrix plot

        # Example for more control over markers:
        from matminer.figrecipes.plotly.make_plots import PlotlyFig
        from matminer.datasets.dataframe_loader import load_elastic_tensor
        df = load_elastic_tensor()
        pf = PlotlyFig()
        pf.scatter_matrix(df[['volume', 'G_VRH', 'K_VRH', 'poisson_ratio']],
                colbar_col='poisson_ratio', text=df['material_id'],
                marker={'symbol': 'diamond', 'size': 8, 'line': {'width': 1,
                'color': 'black'}}, colormap='Viridis',
                title='Elastic Properties Scatter Matrix')
        """
        marker = marker or {'symbol': 'circle-open'}
        nplots = len(df.columns) - int(colbar_col is not None)
        scatter_scale = 1/nplots**0.2
        marker_size = marker.get('size') or 10.0 * scatter_scale * self.marker_scale
        fig = FF.create_scatterplotmatrix(df, index=colbar_col, diag='histogram',
                size=marker_size, height=height, width=width, **kwargs)

        # also update fig layout as scatter plot ignores PlotlyFig layout for some reason
        fig['layout'].update(
            titlefont = {'family': self.fontfamily, 'size': self.textsize*scatter_scale},
            margin = self.margins)

        # update each plot; we don't update the histograms markers as it causes issues:
        for iplot in range(nplots**2):
            fig['data'][iplot].update(hoverinfo=self.hoverinfo)
            for ax in ['x', 'y']:
                fig['layout']['{}axis{}'.format(ax, iplot+1)]['titlefont']['family'] = self.fontfamily
                fig['layout']['{}axis{}'.format(ax, iplot+1)]['titlefont']['size'] = self.textsize * scatter_scale
                fig['layout']['{}axis{}'.format(ax, iplot+1)]['tickfont']['family'] = self.fontfamily
                fig['layout']['{}axis{}'.format(ax, iplot+1)]['tickfont']['size'] = self.textsize * scatter_scale
            if iplot % (nplots+1) != 0:
                fig['data'][iplot].update(marker=marker, text=text)
        self._create_plot(fig)


    def histogram(self, x, histnorm="probability density", x_start=None, x_end=None, bin_size=None,
                  color='rgba(70, 130, 180, 1)', bargap=0):
        """
        Create a histogram using Plotly

        Args:
            x: (list) sample data
            histnorm: (str) Specifies the type of normalization used for this histogram trace. If "", the span of each
                bar corresponds to the number of occurrences (i.e. the number of data points lying inside the bins). If
                "percent", the span of each bar corresponds to the percentage of occurrences with respect to the total
                number of sample points (here, the sum of all bin area equals 100%). If "density", the span of each bar
                corresponds to the number of occurrences in a bin divided by the size of the bin interval (here, the
                sum of all bin area equals the total number of sample points). If "probability density", the span of
                each bar corresponds to the probability that an event will fall into the corresponding bin (here, the
                sum of all bin area equals 1)
            x_start: (float) starting value for x-axis bins. Note: after some testing, this variable does not seem to
                be read by Plotly when set to 0 for the latest version of Plotly as of this commit (Nov'16).
            x_end: (float) end value for x-axis bins
            bin_size: (float) step in-between value of each x axis bin
            color: (str/array) in the format of a (i) color name (eg: "red"), or (ii) a RGB tuple,
                (eg: "rgba(255, 0, 0, 0.8)"), where the last number represents the marker opacity/transparency, which
                must be between 0.0 and 1.0., or (iii) hexagonal code (eg: "FFBAD2")
            bargap: (float) gap between bars

        Returns: a Plotly histogram plot

        """
        if not x_start:
            x_start = min(x)

        if not x_end:
            x_end = max(x)

        if not bin_size:
            bin_size = (x_start - x_end)/10.0

        # plotly fig does not render correctly if x has shape (_, 1), such as the result of a dataframe.as_matrix()
        # The array must have shape (_,).
        if isinstance(x, np.ndarray):
            if len(x.shape) == 2:
                x = x.reshape((len(x),))

        histogram = go.Histogram(x=x, histnorm=histnorm,
                                 xbins=dict(start=x_start, end=x_end, size=bin_size),
                                 marker=dict(color=color))

        data = [histogram]

        self.layout['hovermode'] = 'x'
        self.layout['bargap'] = bargap
        fig = dict(data=data, layout=self.layout)

        self._create_plot(fig)

    def bar_chart(self, x, y):
        """
        Create a bar chart using Plotly

        Args:
            x: (list/numpy array/Pandas series of numbers, strings, or datetimes) sets the x coordinates
            y: (list/numpy array/Pandas series of numbers, strings, or datetimes) sets the y coordinates

        Returns: a Plotly bar chart
        """

        barplot = go.Bar(x=x, y=y)
        data = [barplot]
        fig = dict(data=data, layout=self.layout)
        self._create_plot(fig)

    def sankey(self):
        pass


