all:
	protoc --elm_out=elm-client/src/ --python_out=python/braggle/ --mypy_out=python/braggle/ protobuf/*.proto
	cd elm-client/ && elm make src/Main.elm
	cd python/ && mypy . && pytest .
