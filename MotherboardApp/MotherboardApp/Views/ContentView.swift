import SwiftUI

struct ContentView: View {
    @StateObject private var rackVM = RackViewModel()

    var body: some View {
        TabView {
            RackCarouselView()
                .environmentObject(rackVM)
                .tabItem {
                    Label("層架", systemImage: "server.rack")
                }

            CatalogView()
                .tabItem {
                    Label("目錄", systemImage: "cpu")
                }
        }
    }
}
