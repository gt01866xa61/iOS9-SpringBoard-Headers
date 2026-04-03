import Foundation

struct Rack: Identifiable, Codable {
    let id: UUID
    var name: String
    var levels: Int
    var slotsPerLevel: Int
    var slots: [RackSlot]

    init(name: String, levels: Int, slotsPerLevel: Int) {
        self.id = UUID()
        self.name = name
        self.levels = levels
        self.slotsPerLevel = slotsPerLevel
        self.slots = (1...(levels * slotsPerLevel)).map { RackSlot(position: $0) }
    }

    // Returns slot at given 1-based row and column
    func slot(row: Int, column: Int) -> RackSlot? {
        let position = (row - 1) * slotsPerLevel + column
        return slots.first { $0.position == position }
    }
}
