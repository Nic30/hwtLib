"""
This package contains components, interfaces, data types and other utils
related to Universal Serial Bus (USB) protocol.

The USB bus is composed of Host (the main device which controls the bus), Hub(s) (a port extender) and a Device(s).
The USB protocol stack (v3.2) is composed of multipl layers as depicted in:

.. figure:: ./_static/USB-Protocol-Stack-V3.png

* Functional Layer:

  * This layer generates requests which are converted
    into transactions containing different packets.
    It also manages end to end data flow between host
    and device.

Protocol Layer:

  * Packets originates at transmit part of protocol layer
    and terminates at receive part of protocol layer.
    It has various functions which include following.

    * Ensure end to end reliability of packets.

    * Ensure effective management of power.

    * Ensure effective use of Bandwidth.

Link Layer:

  * This layer manages port to port flow of data between
    USB host and device. Link layer commands ensure link level data integrity,
    flow control and power management. This layer handles packet acknowledgement
    and takes care of error recovery. The Link Layer also handles Header Packet Framing.
    Its functions are similar to MAC layer of OSI model.

Physical Layer:

  * This layer offers actual physical connection between two ports.
    The connection uses a single differential pair (<= USB 2.0) or
    two differential data pairs (>= USB 3.0) (one transmit
    path and one receive path).
    The USB <=2.0 physical layer performs NRZI (Non Return to Zero Invert) encoding and bit stuffing.
    In the USB >=3.0 and <3.2 physical layer the transmit part of physical layer performs
    data scrambling, 8b10b encoding, and serialization functions.
    And the receive part of physical Layer performs de-serialization, 8b10b decoding,
    data descrambling, and receiver clock and data recovery.
    In USB >=3.2 it may have additional RX and TX lane.

:note: USB Documentation, Christopher D. Leary and Devrin TalenDecember 17, 2007

Bus Enumeration

1.  Host waits for at least 100 ms to account for the insertion process.
2.  Host resets the device.  Device should now be at address 0 and the defaultcontrol pipe will be open (default state).
3.  Host queries the device descriptor from the devices default control pipe.
4.  The host controller assigns a unique address to the device.
5.  Host queries all configuration descriptors from the device, then sets one.At this point,
    the device will begin to draw the amount of power requestedby the assigned interface.
6.  Host queries all other remaining descriptors (interface, endpoint, etc.)  andsets up any requested interrupt transfers.


USB Endpoints

In the USB specification, a device endpoint is a uniquely addressable portion of a USB device that is the source
or sink of information in a communication flow between the host and device.
The Ep0 has is dedicated to control and and it provides descriptors for other endpoints.

The Endpoints may support following types of transfer:

* Control
* Interrupt
* Bulk
* Isochronous



.. figure:: ./_static/usb_transaction_example.png
"""