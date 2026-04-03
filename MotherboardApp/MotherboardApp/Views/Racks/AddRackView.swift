import SwiftUI

struct AddRackView: View {
    @EnvironmentObject var rackVM: RackViewModel
    @Environment(\.dismiss) private var dismiss

    @State private var name: String = ""
    @State private var levels: Int = 3
    @State private var slotsPerLevel: Int = 4

    private var totalSlots: Int { levels * slotsPerLevel }

    var body: some View {
        NavigationStack {
            Form {
                Section("層架名稱") {
                    TextField("例如：測試架A", text: $name)
                }

                Section("層架設定") {
                    Stepper("層數：\(levels) 層", value: $levels, in: 1...20)
                    Stepper("每層片數：\(slotsPerLevel) 片", value: $slotsPerLevel, in: 1...10)
                }

                Section {
                    HStack {
                        Text("總槽位")
                        Spacer()
                        Text("\(totalSlots) 個")
                            .foregroundStyle(.secondary)
                    }
                    HStack {
                        Text("位置編號")
                        Spacer()
                        Text("1 → \(totalSlots)")
                            .foregroundStyle(.secondary)
                            .font(.caption)
                    }
                } header: {
                    Text("預覽")
                }
            }
            .navigationTitle("新增層架")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("新增") {
                        let rackName = name.isEmpty ? "層架 \(rackVM.racks.count + 1)" : name
                        rackVM.addRack(name: rackName, levels: levels, slotsPerLevel: slotsPerLevel)
                        dismiss()
                    }
                }
            }
        }
    }
}
