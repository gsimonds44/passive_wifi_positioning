//
//  ContentView.swift
//  positionTracker
//
// -Source code for iOS application-
// This code displays space_image.png and uses target_list.csv to guide the subject through sample locations within the test space.
// The "Capture Position" button is tapped to and send location data over bluetooth to the laptop for logging.
//

import SwiftUI
import CoreBluetooth



class BluetoothPeripheral: NSObject, CBPeripheralManagerDelegate {
    var peripheralManager: CBPeripheralManager?
    var touchCharacteristic: CBMutableCharacteristic?
    var onReceiveLogged: (() -> Void)? // closure to run when "logged" ack is received

    override init() {
        super.init()
        peripheralManager = CBPeripheralManager(delegate: self, queue: nil)
    }

    func peripheralManagerDidUpdateState(_ peripheral: CBPeripheralManager) {
        if peripheral.state == .poweredOn {
            print("Bluetooth is ON")
            
            // create a custom BLE service and characteristic
            let serviceUUID = CBUUID(string: "1234")
            let characteristicUUID = CBUUID(string: "5678")

            touchCharacteristic = CBMutableCharacteristic(
                type: characteristicUUID,
                properties: [.read, .notify, .writeWithoutResponse],
                value: nil,
                permissions: [.readable, .writeable]
            )

            let service = CBMutableService(type: serviceUUID, primary: true)
            service.characteristics = [touchCharacteristic!]

            peripheralManager?.add(service)

            // start BLE advertising
            peripheralManager?.startAdvertising([
                CBAdvertisementDataServiceUUIDsKey: [serviceUUID],
                CBAdvertisementDataLocalNameKey: "MyBLEiPhone",
                CBAdvertisementDataIsConnectable: NSNumber(value: true)
            ])

            print("Started Advertising Touch Data over Bluetooth")
            print("Characteristic Properties: \(touchCharacteristic?.properties.rawValue ?? 0)")
            print("Characteristic Permissions: \(touchCharacteristic?.permissions.rawValue ?? 0)")

        } else {
            print("Bluetooth is NOT available")
        }
    }

    // send position data to computer
    func sendTouchData(x: CGFloat, y: CGFloat, s: Int) {
        guard let characteristic = touchCharacteristic else { return }
        let dataString = "\(Int(s))_\(Int(x))_\(Int(y))"
        if let data = dataString.data(using: .utf8) {
            peripheralManager?.updateValue(data, for: characteristic, onSubscribedCentrals: nil)
            print("Sent: \(dataString)")
        }
    }
    
    // receive "logged" confirmation from PC via BLE write request
    func peripheralManager(_ peripheral: CBPeripheralManager, didReceiveWrite requests: [CBATTRequest]) {
        for request in requests {
            if let value = request.value,
               let string = String(data: value, encoding: .utf8),
               string == "logged" {
                onReceiveLogged?()
            }
        }
    }
}


struct ContentView: View {
    @State private var touchPoint: CGPoint? = nil  // current large red dot position
    @State private var BLEsendTxt: String = ""
    @State private var csvPoints: [CGPoint] = []   // loaded points from CSV
    @State private var csvIndex: Int = 0           // index of current position
    @State private var pastPoints: [[Int]] = []    // history of visited position
    @State private var waitingForAck: Bool = false // flag to block button until PC ack

    let bluetoothPeripheral = BluetoothPeripheral()
    let imageWidth: CGFloat = 238
    let imageHeight: CGFloat = 734
    let cmPerPixel: CGFloat = 1.5  // scale factor to convert pixel to cm

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            VStack(spacing: 10) {
                ZStack {
                    // space floor plan image
                    Image("space_image")
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: imageWidth, height: imageHeight)

                    // draw small red dots for previously visited positions
                    ForEach(pastPoints.indices, id: \.self) { i in
                        let x = CGFloat(pastPoints[i][0])
                        let y = CGFloat(pastPoints[i][1])
                        Circle()
                            .fill(Color.red)
                            .frame(width: 3, height: 3)
                            .position(x: x, y: y)
                    }

                    // Capture Button: Sends next target to PC, waits for ack before continuing
                    if let point = touchPoint {
                        Circle()
                            .fill(Color.red)
                            .frame(width: 10, height: 10)
                            .position(point)
                    }
                }
                .frame(width: imageWidth, height: imageHeight)
                HStack(spacing: 30) {
                    // overwrite old positions
                    Button("<") {
                        pastPoints.removeLast()
                        csvIndex -= 1
                        touchPoint = csvPoints[csvIndex]
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(csvIndex <= 0 ? Color.gray.opacity(0.6) : Color.blue.opacity(0.8))
                    .cornerRadius(5)
                    .foregroundColor(.white)
                    .disabled(csvIndex <= 0)
                    
                    // initiate data capture for current position, and advance to next
                    Button("Capture Target (\(csvIndex))") {
                        print(csvIndex)
                        if waitingForAck { return } // prevent next press until previous snapshot is saved by computer
                        
                        if csvPoints.isEmpty {
                            csvPoints = loadCSVPoints()
                        }
                        
                        if csvIndex < csvPoints.count && csvIndex >= 0{
                            let point_0 = csvPoints[csvIndex]
                            
                            pastPoints.append([Int(point_0.x), Int(point_0.y)])
                            bluetoothPeripheral.sendTouchData(x: point_0.x*cmPerPixel, y: point_0.y*cmPerPixel, s: csvIndex)
                            waitingForAck = true
                        } else {
                            print("CSV finished.")
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 5)
                    .background(waitingForAck || csvIndex >= csvPoints.count ? Color.gray.opacity(0.6) : Color.blue.opacity(0.8))
                    .cornerRadius(5)
                    .foregroundColor(.white)
                    .disabled(waitingForAck || csvIndex >= csvPoints.count)
                    
                    // skip to next position
                    Button(">") {
                        let point_0 = csvPoints[csvIndex]
                        pastPoints.append([Int(point_0.x), Int(point_0.y)])
                        csvIndex += 1
                        touchPoint = csvPoints[csvIndex]
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(csvIndex >= csvPoints.count-1 ? Color.gray.opacity(0.6) : Color.blue.opacity(0.8))
                    .cornerRadius(5)
                    .foregroundColor(.white)
                    .disabled(csvIndex >= csvPoints.count-1)
                }
                    

            }
        }
        .onAppear {
            // handle ack from PC over BLE
            bluetoothPeripheral.onReceiveLogged = {
                DispatchQueue.main.async {
                    print("Received 'logged'")
                    csvIndex += 1
                    waitingForAck = false
                }
                
                // preload the next position
                var point_1 = csvPoints[csvIndex]
                if csvIndex != csvPoints.count-1{
                    point_1 = csvPoints[csvIndex+1]
                }
                if csvIndex < csvPoints.count {
                    touchPoint = point_1
                }
            }
            
            // load and show first position
            if csvPoints.isEmpty {
                csvPoints = loadCSVPoints()
            }
            if csvIndex < csvPoints.count {
                touchPoint = csvPoints[csvIndex]
            }
        }
    }

    func loadCSVPoints() -> [CGPoint] {
        guard let url = Bundle.main.url(forResource: "target_list", withExtension: "csv") else {
            return []
        }
        do {
            // normalize newline characters
            var content = try String(contentsOf: url)
            content = content.replacingOccurrences(of: "\r\n", with: "\n")
            content = content.replacingOccurrences(of: "\r", with: "\n")

            let lines = content.split(separator: "\n")

            return lines.compactMap { line in
                let parts = line.split(separator: ",")
                if parts.count == 2,
                   let x = Double(parts[0].trimmingCharacters(in: .whitespaces)),
                   let y = Double(parts[1].trimmingCharacters(in: .whitespaces)) {
                    return CGPoint(x: x, y: y)
                }
                return nil
            }
        } catch {
            return []
        }
    }
}
