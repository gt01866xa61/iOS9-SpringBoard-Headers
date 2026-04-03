import SwiftUI

struct RackGridView: View {
    let rack: Rack
    let rackIndex: Int
    @EnvironmentObject var rackVM: RackViewModel

    @State private var assignSlotPosition: Int?
    @State private var actionSlot: RackSlot?
    @State private var showActionSheet = false

    var body: some View {
        ScrollView {
            LazyVGrid(
                columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: rack.slotsPerLevel),
                spacing: 8
            ) {
                ForEach(rack.slots.sorted(by: { $0.position < $1.position })) { slot in
                    let model = rackVM.resolveModel(for: slot)
                    SlotView(
                        slot: slot,
                        rackIndex: rackIndex,
                        model: model,
                        onTap: {
                            if model != nil {
                                actionSlot = slot
                                showActionSheet = true
                            } else {
                                assignSlotPosition = slot.position
                            }
                        }
                    )
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
        .sheet(isPresented: Binding(
            get: { assignSlotPosition != nil },
            set: { if !$0 { assignSlotPosition = nil } }
        )) {
            if let position = assignSlotPosition {
                SlotAssignView(rackID: rack.id, slotPosition: position, rackIndex: rackIndex)
                    .environmentObject(rackVM)
            }
        }
        .confirmationDialog(
            actionSlot.map { "位置 \(rackIndex)-\($0.position)" } ?? "主機板操作",
            isPresented: $showActionSheet,
            titleVisibility: .visible
        ) {
            if let slot = actionSlot, let model = rackVM.resolveModel(for: slot) {
                Link("查看官網規格", destination: model.productURL)
                Button("更換主機板") {
                    showActionSheet = false
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        assignSlotPosition = slot.position
                    }
                }
                Button("清除此槽位", role: .destructive) {
                    rackVM.clearSlot(position: slot.position, in: rack.id)
                }
            }
            Button("取消", role: .cancel) {}
        } message: {
            if let slot = actionSlot, let model = rackVM.resolveModel(for: slot) {
                Text(model.name)
            }
        }
    }
}
