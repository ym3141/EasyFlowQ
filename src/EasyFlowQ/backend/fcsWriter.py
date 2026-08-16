'''
Writer for FCS3.1 files.

The bundled FlowCal package (``..FlowCal``) only reads FCS files, so this module
implements the writing side. It is used to export the events that survive the
currently applied gates back into an FCS file, so that gated populations can be
handed to other flow cytometry software.

Note that the data held in memory has already been converted to RFI (see
``ioData.processFCS2List``), and may have been compensated and extended with
derived parameters. The exported file therefore describes linear, un-gained
data: ``$PnE`` is written as ``0,0``, ``$PnG`` and ``$SPILLOVER`` are dropped,
and ``$DATATYPE`` is a floating point type.
'''

import math
import re
from os import path

import numpy as np

from ..FlowCal.io import encoding
from .. import __version__

# Length of the FCS HEADER segment: 6 bytes of version, 4 spaces, and 6
# right-justified 8-byte offsets.
_headerLength = 58

# Largest offset that fits in an 8-byte HEADER field. Larger offsets are written
# as 0 in the HEADER, and read from $BEGINDATA/$ENDDATA instead.
_maxHeaderOffset = 99999999

# The offsets of the DATA segment depend on the length of the TEXT segment,
# which in turn contains those offsets. Writing them zero-padded to a fixed
# width breaks the circularity: the TEXT segment has the same length whatever
# the offsets turn out to be.
_offsetWidth = 10

_dataTypeDtypes = {'F': np.dtype('<f4'), 'D': np.dtype('<f8')}

# Keywords describing the layout of the file being written. These are always
# regenerated, never copied from the source sample.
_regeneratedKeywords = {
    '$BEGINANALYSIS', '$BEGINDATA', '$BEGINSTEXT', '$BYTEORD', '$DATATYPE',
    '$ENDANALYSIS', '$ENDDATA', '$ENDSTEXT', '$FIL', '$MODE', '$NEXTDATA',
    '$PAR', '$TOT',
}

# Keywords that no longer describe the exported data. The events are gated, and
# possibly compensated, so spillover matrices and subsetting info copied from
# the source file would be actively misleading.
_droppedKeywords = {
    '$SPILLOVER', 'SPILLOVER', 'SPILL', '$COMP', '$CSMODE', '$CSVBITS',
    '$CSVnFLAG', '$UNICODE',
}

# Per-parameter keywords ($P1N, $P12S, $PK3, ...). Gating and derived parameters
# can change the channel list, so these are rebuilt from the sample's metadata.
_perParamPattern = re.compile(r'^\$P(K|KN)?\d+[A-Z]*$', re.IGNORECASE)

# Delimiter candidates, in order of preference. The first one that appears in no
# keyword or value is used, which avoids relying on delimiter escaping.
_delimCandidates = ('/', '|', '!', '#', '%', '&', '@', '~', '^', '\x0c', '\x1c')


def _cleanValue(value):
    '''
    Render `value` as a keyword value that is legal in a TEXT segment.

    Null bytes and the characters used to pad the segment are removed, and the
    result is stripped. FCS3.1 forbids empty keyword values, so callers should
    skip keywords for which this returns an empty string.
    '''
    return str(value).replace('\x00', '').strip()


def _pickDelimiter(pairs):
    for candidate in _delimCandidates:
        if not any(candidate in string for pair in pairs for string in pair):
            return candidate

    # Every candidate is in use. Fall back to the conventional delimiter and let
    # _serializeText escape it by doubling, as the FCS standards prescribe.
    return _delimCandidates[0]


def _serializeText(pairs, delim):
    chunks = [delim]
    for key, value in pairs:
        chunks.append(key.replace(delim, delim * 2))
        chunks.append(delim)
        chunks.append(value.replace(delim, delim * 2))
        chunks.append(delim)

    return ''.join(chunks).encode(encoding, errors='replace')


def _headerBytes(textBegin, textEnd, dataBegin, dataEnd):
    offsets = [textBegin, textEnd, dataBegin, dataEnd, 0, 0]
    # Offsets that do not fit in the HEADER are written as 0 there; readers are
    # required to fall back on $BEGINDATA/$ENDDATA in that case.
    fields = ''.join('{0:>8}'.format(offset if offset <= _maxHeaderOffset else 0)
                     for offset in offsets)

    return ('FCS3.1' + ' ' * 4 + fields).encode(encoding)


def _channelRange(fcsData, chnlIdx, data):
    '''
    Pick the $PnR value for channel `chnlIdx`.

    The sample's declared range is preferred, so that the exported file keeps
    the scale of the original acquisition rather than the (narrower) range of
    whatever subset of events survived gating. The largest value actually
    present is used as a floor, since $PnR is meant to bound the data.
    '''
    top = None

    try:
        declared = fcsData.range()[chnlIdx][1]
        if np.isfinite(declared):
            top = float(declared)
    except (AttributeError, IndexError, TypeError, ValueError):
        pass

    if data.shape[0]:
        dataTop = float(np.nanmax(data[:, chnlIdx]))
        if np.isfinite(dataTop):
            top = dataTop if top is None else max(top, dataTop)

    if top is None or not np.isfinite(top):
        return 1

    return max(1, int(math.ceil(top + 1)))


def _optionalFloat(values, chnlIdx):
    '''
    Return `values[chnlIdx]` as a float, or None if it isn't a usable number.

    Derived parameters carry the string 'N/A' for the per-channel hardware
    settings, and channels of the source file may carry nothing at all.
    '''
    try:
        value = float(values[chnlIdx])
    except (IndexError, TypeError, ValueError):
        return None

    return value if np.isfinite(value) else None


def _paramPairs(fcsData, data, dtype):
    channels = [str(chnl) for chnl in fcsData.channels]

    try:
        labels = list(fcsData.channel_labels())
    except (AttributeError, TypeError):
        labels = [None] * len(channels)

    try:
        voltages = list(fcsData.detector_voltage())
    except (AttributeError, TypeError):
        voltages = [None] * len(channels)

    pairs = []
    for chnlIdx, chnl in enumerate(channels):
        n = chnlIdx + 1
        pairs.append(('$P{0}N'.format(n), chnl))
        pairs.append(('$P{0}B'.format(n), str(dtype.itemsize * 8)))
        # The data is already in RFI, i.e. linearized and un-gained, so it is
        # described as linear here. $PnG is deliberately not written: repeating
        # the acquisition gain would make readers divide by it a second time.
        pairs.append(('$P{0}E'.format(n), '0,0'))
        pairs.append(('$P{0}R'.format(n), str(_channelRange(fcsData, chnlIdx, data))))

        label = _cleanValue(labels[chnlIdx]) if chnlIdx < len(labels) and labels[chnlIdx] else ''
        if label.startswith('Derived Parameter'):
            label = 'Derived' + label[len('Derived Parameter'):]
        if label:
            pairs.append(('$P{0}S'.format(n), label))

        voltage = _optionalFloat(voltages, chnlIdx)
        if voltage is not None:
            pairs.append(('$P{0}V'.format(n), repr(voltage)))

    return pairs


def _carriedPairs(fcsData):
    '''
    Keywords copied over from the source sample's TEXT segment.
    '''
    try:
        sourceText = fcsData.text
    except AttributeError:
        return []

    if not sourceText:
        return []

    pairs = []
    for key in sorted(sourceText):
        upperKey = key.upper()
        if upperKey in _regeneratedKeywords or upperKey in _droppedKeywords:
            continue
        if _perParamPattern.match(key):
            continue

        value = _cleanValue(sourceText[key])
        if value:
            pairs.append((key, value))

    return pairs


def _dedupPairs(pairs):
    '''
    Collapse repeated keywords, keeping the last value and the first position.

    A TEXT segment may not contain the same keyword twice, and later sources
    (caller supplied keywords) are more specific than earlier ones (keywords
    copied from the source file).
    '''
    merged = {}
    for key, value in pairs:
        merged[key.upper()] = (key, value)

    return list(merged.values())


def writeFCS(filePath, fcsData, extraKeywords=None, dataType='F'):
    '''
    Write `fcsData` to `filePath` as an FCS3.1 file.

    Parameters
    ----------
    filePath : str
        Path of the file to write.
    fcsData : FCSData
        Events to write. Channel names, labels and metadata are taken from this
        object, so a gated (sliced) sample can be passed directly.
    extraKeywords : dict, optional
        Additional keywords to store in the TEXT segment. These override
        keywords copied from the source sample, but not the ones describing the
        layout of the file.
    dataType : {'F', 'D'}, optional
        $DATATYPE of the written file: single ('F') or double ('D') precision
        floating point. Defaults to 'F', which every reader supports.
    '''
    if dataType not in _dataTypeDtypes:
        raise ValueError('dataType should be one of {0}, not {1}'.format(
            sorted(_dataTypeDtypes), dataType))
    dtype = _dataTypeDtypes[dataType]

    data = np.ascontiguousarray(np.asarray(fcsData), dtype=dtype)
    if data.ndim == 1:
        data = data.reshape((data.shape[0], 1))
    if data.ndim != 2:
        raise ValueError('fcsData should be a NxD array of events')
    nEvents, nChnls = data.shape

    if nChnls != len(fcsData.channels):
        raise ValueError('fcsData has {0} columns but {1} channels'.format(
            nChnls, len(fcsData.channels)))

    paramPairs = _paramPairs(fcsData, data, dtype)
    carriedPairs = _carriedPairs(fcsData)
    extraPairs = [(key, _cleanValue(value))
                  for key, value in (extraKeywords or {}).items()
                  if _cleanValue(value)]

    def buildTextBytes(beginData, endData):
        pairs = [
            ('$BEGINANALYSIS', '0'),
            ('$ENDANALYSIS', '0'),
            ('$BEGINSTEXT', '0'),
            ('$ENDSTEXT', '0'),
            ('$BEGINDATA', '{0:0{1}d}'.format(beginData, _offsetWidth)),
            ('$ENDDATA', '{0:0{1}d}'.format(endData, _offsetWidth)),
            ('$BYTEORD', '1,2,3,4'),
            ('$DATATYPE', dataType),
            ('$MODE', 'L'),
            ('$NEXTDATA', '0'),
            ('$PAR', str(nChnls)),
            ('$TOT', str(nEvents)),
            ('$FIL', path.basename(filePath)),
        ] + paramPairs + carriedPairs + extraPairs

        pairs = _dedupPairs(pairs)
        return _serializeText(pairs, _pickDelimiter(pairs))

    # First pass only measures the TEXT segment; the placeholder offsets are
    # zero-padded to the same width as the real ones, so the second pass
    # produces a segment of exactly the same length.
    textLength = len(buildTextBytes(0, 0))
    dataBegin = _headerLength + textLength
    # The offsets are inclusive, so a sample whose every event was gated out
    # ends up with $ENDDATA one before $BEGINDATA, i.e. a zero byte segment.
    dataEnd = dataBegin + data.nbytes - 1

    textBytes = buildTextBytes(dataBegin, dataEnd)
    if len(textBytes) != textLength:
        raise RuntimeError('TEXT segment length changed while writing offsets')

    header = _headerBytes(_headerLength, _headerLength + textLength - 1,
                          dataBegin, dataEnd)

    with open(filePath, 'wb') as outFile:
        outFile.write(header)
        outFile.write(textBytes)
        data.tofile(outFile)


def exportKeywords(sourceName=None, gateNames=None, compensated=None):
    '''
    Build the EasyFlowQ provenance keywords for an exported FCS file.

    These record what was done to the events before they were written, which is
    not recoverable from the data itself.
    '''
    keywords = {'CREATOR': 'EasyFlowQ {0}'.format(__version__)}

    if sourceName:
        keywords['EASYFLOWQ_SOURCE'] = sourceName
    if gateNames is not None:
        keywords['EASYFLOWQ_GATES'] = ', '.join(gateNames) if gateNames else 'None'
    if compensated is not None:
        keywords['EASYFLOWQ_COMPENSATED'] = 'True' if compensated else 'False'

    # to_rfi is applied to every sample on load, see ioData.processFCS2List.
    keywords['EASYFLOWQ_TRANSFORM'] = 'RFI'

    return keywords
