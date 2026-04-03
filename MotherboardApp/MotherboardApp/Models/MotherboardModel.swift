import Foundation

struct MotherboardModel: Identifiable, Hashable {
    let id: String
    let name: String
    let brandID: String
    let chipsetID: String
    let series: String
    let productURL: URL
}
