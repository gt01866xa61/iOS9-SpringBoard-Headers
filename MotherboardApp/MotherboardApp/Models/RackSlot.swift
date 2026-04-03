import Foundation

struct RackSlot: Identifiable, Codable, Hashable {
    let id: UUID
    let position: Int   // 1-based, left-to-right, top-to-bottom
    var modelID: String?

    init(position: Int, modelID: String? = nil) {
        self.id = UUID()
        self.position = position
        self.modelID = modelID
    }
}
