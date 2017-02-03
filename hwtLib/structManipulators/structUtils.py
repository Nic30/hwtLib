
class StructFieldPart():
    def __init__(self, wordIndex, busWordBitRange, inFieldBitRange):
        """ranges in little endian notation"""
        self.wordIndex = wordIndex   
        self.busWordBitRange = busWordBitRange 
        self.inFieldBitRange = inFieldBitRange
        
    def getSignal(self, busDataSignal):
        if self.busWordBitRange == (busDataSignal._dtype.bit_length(), 0):
            return busDataSignal
        else:
            return busDataSignal[self.busWordBitRange[0]:self.busWordBitRange[1]]

    def __repr__(self):
        return "<StructFieldPart, wordIndex:%d, busWordBitRange:%r, inFieldBitRange:%r>" % (
                self.wordIndex, self.busWordBitRange, self.inFieldBitRange)
    
        
class StructFieldInfo():
    def __init__(self, typ, name):
        self.type = typ
        self.name = name
        self.interface = None
        self.parts = []
    
    def discoverFieldParts(self, busDataWidth, startBitIndex):
        """Some fields has to be internally split due data-width of bus,
        there we discover how to split field to words on bus
        
        @param startWordIndex: bit index where field starts, (f.e. 16 for f2 in struct {uint16_t f1, uint16_t f2})
        
        """
        fieldWidth = self.type.bit_length()
        inFieldOffset = 0
        
        while fieldWidth != 0:
            wordIndex = startBitIndex // busDataWidth
            bitRangeOfWord = (busDataWidth * (wordIndex + 1), startBitIndex)  # little-endian
            widthOfPart = min(bitRangeOfWord[0], startBitIndex + fieldWidth) - startBitIndex
            busWordBitOffset = startBitIndex % busDataWidth
            
            busWordBitRange = (busWordBitOffset + widthOfPart, busWordBitOffset)
            inFieldRange = (inFieldOffset + widthOfPart, inFieldOffset)
            
            fp = StructFieldPart(wordIndex, busWordBitRange, inFieldRange)
            self.parts.append(fp)
            
            inFieldOffset += widthOfPart
            startBitIndex += widthOfPart
            fieldWidth -= widthOfPart
            
        return startBitIndex + fieldWidth
    
    def __repr__(self):
        return "<StructFieldInfo %s, %r, parts:%s  >" % (
            self.name, self.type, "\n".join(["%r" % s for s in self.parts]))
    
class StructBusBurstInfo():
    """
    Represents data chunks(bursts) which should be send over interface
    container of parts of fields form struct
    """
    def __init__(self, addrOffset, fieldInfos):
        """
        @param addrOffset: offset of this burst in number of words
        @param fieldInfos: iterable of field StructFieldInfo 
        """
        self.addrOffset = addrOffset
        self.fieldInfos = fieldInfos
    
    def wordCnt(self):
        firstWordIndex = self.fieldInfos[0].parts[0].wordIndex
        lastWordIndex = self.fieldInfos[-1].parts[-1].wordIndex
        
        return lastWordIndex - firstWordIndex + 1
        
    @staticmethod
    def packFieldInfosToBusBurst(structInfos, maxDummyWords, wordIndexToAddrRatio):
        """
        @param structInfos: iterable of StructFieldInfo which are describing target structure
        @param maxDummyWords: maximum allowable not used words in bus burst
        @param wordIndexToAddrRatio: addrOffset = wordIndex of field * wordIndexToAddrRatio
        @return: list of StructBusBurstInfo
        """
        busBursts = []
        
        try:
            firstWordIndex = structInfos[0].parts[0].wordIndex
        except IndexError:
            return []
        
        lastWordIndex = firstWordIndex    
        actual = StructBusBurstInfo(lastWordIndex*wordIndexToAddrRatio, [])
        skippedWords = 0
        busBursts.append(actual)
        
        # for each part which should be download
        for info in structInfos:
            # check if space between fields is small enough
            startW = info.parts[0].wordIndex
            if startW - lastWordIndex > maxDummyWords:
                # space between useful fields is too big and we have to split burst into multiple smaller
                skippedWords += startW - lastWordIndex - 2
                actual = StructBusBurstInfo(startW * wordIndexToAddrRatio, [])
                busBursts.append(actual)
            
            if skippedWords != 0:        
                # update word indexes after unused fields were potentially cut of
                for p in info.parts:
                    p.wordIndex -= skippedWords
            
            actual.fieldInfos.append(info)
            lastWordIndex = info.parts[-1].wordIndex
        
        
        return busBursts

    @staticmethod
    def sumOfWords(structBusBurstInfos):
        return structBusBurstInfos[-1].fieldInfos[-1].parts[-1].wordIndex + 1
    
    def __repr__(self):
        return "<StructBusBurstInfo addrOffset:%d>" % self.addrOffset
        
def selectFieldsFromTmpl(structTemplate, fieldsToUse):
    template = []
    fieldsToUse = set(fieldsToUse)
    foundNames = set()
    
    for typ, name in  structTemplate:
        if name not in fieldsToUse:
            name = None
        template.append((typ, name))
        foundNames.add(name)
        
    assert fieldsToUse.issubset(foundNames)
    
    return template   
