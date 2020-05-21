from hwt.synthesizer.interface import Interface


class ChiRN(Interface):
    """
    AMBA 5 CHI (Coherent Hub Interface) for Request Node
    """
    def _declr(self):
        self.tx = ChiRNTx()
        self.rx = ChiRNRx()


class ChiRNTx(Interface):
    """
    AMBA 5 CHI (Coherent Hub Interface) for Request Node tx channels

    :ivar tx_req: Outbound Request.
    :ivar tx_dat: Outbound Data.
        Used for write data, atomic data, snoop data, forward data.
    :ivar tx_rsp: Outbound Response.
        Used for Snoop Response and Completion Acknowledge.
    """
    def _declr(self):
        self.tx_req = ChiReq()
        self.tx_dat = ChiWDat()
        self.tx_rsp = ChiSRsp()


class ChiRNRx(Interface):
    """
    AMBA 5 CHI (Coherent Hub Interface) for Request Node rx channels

    :ivar rsp: Inbound Response.
        Used for responses from the Completer.
    :ivar dat: Inbound Data.
        Used for read data, atomic data.
    :ivar snp: Inbound Snoop Request.
    """
    def _declr(self):
        self.rsp = ChiCRsp()
        self.dat = ChiRDat()
        self.snp = ChiSnp()


class ChiSN(Interface):
    """
    AMBA 5 CHI (Coherent Hub Interface) for Slave Node
    """
    def _declr(self):
        self.tx = ChiSNTx()
        self.rx = ChiSNRx()


class ChiSNRx(Interface):
    """
    AMBA 5 CHI (Coherent Hub Interface) for Slave Node rx channels

    :ivar rsp: Inbound Request.
    :ivar dat: Inbound Data
        Used for write data, atomic data.
    :ivar snp: Inbound Snoop Request.
    """
    def _declr(self):
        self.req = ChiReq()
        self.dat = ChiWDat()


class ChiSNTx(Interface):
    """
    AMBA 5 CHI (Coherent Hub Interface) for Slave Node tx channels

    :ivar rsp: Outbound Response.
        Used for responses from the Completer.
    :ivar dat: Outbound Data.
        Used for read data, atomic data.
    """
    def _declr(self):
        self.rsp = ChiCRsp()
        self.dat = ChiRDat()

