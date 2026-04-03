import Foundation

@MainActor
final class RackViewModel: ObservableObject {
    @Published var racks: [Rack] = []
    @Published var currentRackIndex: Int = 0

    private let userDefaultsKey = "racks_v1"

    init() {
        load()
    }

    // MARK: - Rack Management

    func addRack(name: String, levels: Int, slotsPerLevel: Int) {
        let rack = Rack(name: name, levels: levels, slotsPerLevel: slotsPerLevel)
        racks.append(rack)
        currentRackIndex = racks.count - 1
        save()
    }

    func deleteRack(id: UUID) {
        racks.removeAll { $0.id == id }
        if currentRackIndex >= racks.count {
            currentRackIndex = max(0, racks.count - 1)
        }
        save()
    }

    // MARK: - Slot Management

    func assignModel(_ modelID: String, to slotPosition: Int, in rackID: UUID) {
        guard let rackIndex = racks.firstIndex(where: { $0.id == rackID }),
              let slotIndex = racks[rackIndex].slots.firstIndex(where: { $0.position == slotPosition })
        else { return }
        racks[rackIndex].slots[slotIndex].modelID = modelID
        save()
    }

    func clearSlot(position: Int, in rackID: UUID) {
        guard let rackIndex = racks.firstIndex(where: { $0.id == rackID }),
              let slotIndex = racks[rackIndex].slots.firstIndex(where: { $0.position == position })
        else { return }
        racks[rackIndex].slots[slotIndex].modelID = nil
        save()
    }

    func resolveModel(for slot: RackSlot) -> MotherboardModel? {
        guard let modelID = slot.modelID else { return nil }
        return MotherboardCatalog.model(for: modelID)
    }

    // MARK: - Persistence

    private func save() {
        if let data = try? JSONEncoder().encode(racks) {
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        }
    }

    private func load() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey),
              let decoded = try? JSONDecoder().decode([Rack].self, from: data)
        else { return }
        racks = decoded
    }
}
