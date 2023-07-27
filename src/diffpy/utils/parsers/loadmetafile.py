#!/usr/bin/env python
##############################################################################
#
# diffpy.utils      by DANSE Diffraction group
#                   Simon J. L. Billinge
#                   (c) 2010 The Trustees of Columbia University
#                   in the City of New York.  All rights reserved.
#
# File coded by:
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE_DANSE.txt for license information.
#
##############################################################################

import pathlib
import json

from diffpy.utils.parsers import loadData

# FIXME: add support for yaml, xml
supported_formats = ['.json']


def load_PDF_into_db(dbname, pdfname, hddata: dict, rv: list, oneline=True, show_path=True):
    """Load PDF header and base data into a database file.

    Requires hdata and rv generated from loadData.

    dbname      -- name of the database file to load into.
    pdfname     -- name of the PDF file.
    hddata      -- Dictionary of PDF metadata generated by loadData.
    rv          -- List of PDF (r, gr) pairs generated by loadData.
    oneline     -- store r and gr arrays in a single line for compactness (default True).
    show_path   -- include a PDF_path element in the database entry (default True).
    """
    # new file or update
    existing = False
    if pathlib.Path.is_file(dbname):
        existing = True

    # collect entry
    with open(pdfname, 'r') as grfile:
        data = {}

        # add path
        grpath = grfile.name
        if show_path:
            data.update({'PDF_path': grpath})

        # add r, gr, and header metadata
        if oneline:
            data.update({'r': str(list(rv[:, 0])), 'gr': str(list(rv[:, 1]))})
        else:
            data.update({'r': list(rv[:, 0]), 'gr': list(rv[:, 1])})
        data.update(hddata)

        # parse name using pathlib and generate json entry
        name = pathlib.Path(grpath).name
        entry = {name: data}

    # check if supported type
    extension = pathlib.Path(dbname).suffix
    if extension not in supported_formats:
        raise Exception(f"Format of {dbname} is not supported.")

    # json
    if extension == '.json':
        # dump if non-existing
        if not existing:
            with open(dbname, 'w') as jsonfile:
                jsonfile.write(json.dumps(entry, indent=2))

        # update if existing
        else:
            with open(dbname, 'r') as json_read:
                pdfs = json.load(json_read)
                pdfs.update(entry)
            with open(dbname, 'w') as json_write:
                # dump to string first for formatting
                json.dump(pdfs, json_write, indent=2)


def markup_PDF(muname, hddata: dict, rv: list):
    # FIXME: for REST API, remove if better ways to implement
    """Put PDF file information in a markup language file.

    mumane  -- name of markup file to put data into.
    hddata  -- Dictionary of metadata.
    rv      -- List of (r, gr) pairs.
    """

    # gather data
    data = {}
    data.update({'r': str(list(rv[:, 0])), 'gr': str(list(rv[:, 1]))})
    data.update(hddata)
    extension = pathlib.Path(muname).suffix
    if extension not in supported_formats:
        raise Exception(f"Format of {muname} is not supported.")

    # dumps into file, automatically overwrites
    if extension == '.json':
        with open(muname, 'w') as json_write:
            json.dump(data, json_write, indent=2)


def apply_schema(filename, schemaname, multiple_entries=False):
    """ Reformat a file so relevant entries match the same order as a schema file.
    Other entries are put at the end in the same order.

    filename            -- name of file to apply the schema to.
    schemaname          -- name of schema to apply.
    multiple_entries    -- True if database file (i.e. those generated by load_PDF_into_db).
                           False if data from a single file (i.e. those generated by markup_PDF).
    """

    # ensure proper extension
    file_ext = pathlib.Path(filename).suffix
    schema_ext = pathlib.Path(schemaname).suffix
    if file_ext != schema_ext:
        return Exception("Schema type does not match file type.")
    if file_ext not in supported_formats:
        return Exception(f"Format of {filename} is not supported.")

    # json
    if file_ext == ".json":
        with open(schemaname, 'r') as jsonschema:
            schema = json.load(jsonschema)
            schema_order = []
            for dp in schema:
                schema_order.append(dp)

        # database file
        if multiple_entries:
            # reformat each entry in a collection
            with open(filename, 'r') as json_read:
                data_dict = json.load(json_read)
                reformatted_dict = {}  # new dictionary for entire json
                for entry in data_dict.keys():
                    # reformat each entry
                    entry_dict = data_dict.get(entry)
                    reformatted_entry = {}  # new dictionary for a particular entry
                    for dp in schema_order:
                        if dp in entry_dict:
                            reformatted_entry.update({dp: entry_dict.get(dp)})
                            entry_dict.pop(dp)
                    reformatted_entry.update(entry_dict)
                    reformatted_dict.update({entry: reformatted_entry})
            with open(filename, 'w') as json_write:
                json.dump(reformatted_dict, json_write, indent=2)

        # single file
        else:
            with open(filename, 'r') as json_read:
                data_dict = json.load(json_read)
                reformatted_dict = {}
                # reformat
                for dp in schema_order:
                    if dp in data_dict:
                        reformatted_dict.update({dp: data_dict.get(dp)})
                        data_dict.pop(dp)
                reformatted_dict.update(data_dict)
            with open(filename, 'w') as json_write:
                json.dump(reformatted_dict, json_write, indent=2)
